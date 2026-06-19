from datetime import timedelta

from flask import Blueprint, request, jsonify

from app.extensions import db
from app.models import (
    Teacher, Classroom, Laptop, Issue, IssueItem,
    STATUS_FREE, STATUS_ISSUED, utcnow,
)

# Префикс /api — фронт обращается к /api/teachers, /api/laptops и т.д.
api = Blueprint("api", __name__, url_prefix="/api")


def normalize(text):
    # Приводим к единому виду для сравнения: убираем регистр и лишние пробелы.
    return " ".join(str(text or "").strip().lower().split())


def student_key(full_name, group):
    # Уникальный "отпечаток" ученика: ФИО + группа. По нему проверяем правило
    # "один ученик группы держит максимум один ноутбук".
    return f"{normalize(full_name)}::{normalize(group)}"


@api.get("/health")
def health():
    # Простой эндпоинт "жив ли сервер" — удобно для проверки и деплоя.
    return jsonify({"status": "ok"})


@api.get("/teachers")
def get_teachers():
    rows = Teacher.query.order_by(Teacher.lname, Teacher.fname).all()
    return jsonify([t.to_dict() for t in rows])


@api.get("/classrooms")
def get_classrooms():
    rows = Classroom.query.order_by(Classroom.name).all()
    return jsonify([c.to_dict() for c in rows])


@api.get("/laptops")
def get_laptops():
    rows = Laptop.query.order_by(Laptop.number).all()
    return jsonify([item.to_dict() for item in rows])


@api.post("/issues")
def create_issue():
    """Создать выдачу (1-10 ноутбуков). Здесь же — все бизнес-проверки."""
    data = request.get_json() or {}
    teacher_id = data.get("teacher_id")
    classroom_id = data.get("classroom_id")
    subject_name = (data.get("subject_name") or "").strip()
    items = data.get("items") or []

    # --- обязательные поля шапки ---
    if not teacher_id or not classroom_id or not subject_name:
        return jsonify({"error": "Укажите преподавателя, аудиторию и название пары."}), 400

    # --- размер выдачи 1..10 ---
    if not 1 <= len(items) <= 10:
        return jsonify({"error": "В одной выдаче должно быть от 1 до 10 ноутбуков."}), 400

    if db.session.get(Teacher, teacher_id) is None:
        return jsonify({"error": "Преподаватель не найден."}), 404
    if db.session.get(Classroom, classroom_id) is None:
        return jsonify({"error": "Аудитория не найдена."}), 404

    # --- один ноутбук не может встречаться в запросе дважды ---
    laptop_ids = [it.get("laptop_id") for it in items]
    if len(laptop_ids) != len(set(laptop_ids)):
        return jsonify({"error": "Один и тот же ноутбук нельзя выдать дважды в одной выдаче."}), 400

    # --- один ученик не может встречаться в запросе дважды ---
    request_keys = [student_key(it.get("student_full_name"), it.get("student_group")) for it in items]
    if len(request_keys) != len(set(request_keys)):
        return jsonify({"error": "Ученик из одной группы не может получить два ноутбука."}), 400

    # --- проверяем сами ноутбуки: существуют и свободны ---
    laptops = {}
    for lid in laptop_ids:
        laptop = db.session.get(Laptop, lid)
        if laptop is None:
            return jsonify({"error": f"Ноутбук id={lid} не найден."}), 400
        if laptop.status != STATUS_FREE:
            return jsonify({"error": f"Ноутбук NB-{laptop.number:03d} уже занят."}), 409
        laptops[lid] = laptop

    # --- правило: ученик уже держит активный ноутбук? ---
    active_keys = {
        student_key(it.student_full_name, it.student_group)
        for it in IssueItem.query.filter_by(returned_at=None).all()
    }
    for key in request_keys:
        if key in active_keys:
            # Английская фраза "already has a laptop" — её фронт ловит отдельно.
            return jsonify({"error": "Student already has a laptop."}), 409

    # --- всё проверено: создаём выдачу и позиции одной транзакцией ---
    now = utcnow()
    issue = Issue(
        teacher_id=teacher_id,
        classroom_id=classroom_id,
        subject_name=subject_name,
        created_at=now,
        expires_at=now + timedelta(days=7),
    )
    db.session.add(issue)
    db.session.flush()  # получаем issue.id для позиций

    for it in items:
        cond = (it.get("condition") or "").strip()
        db.session.add(IssueItem(
            issue_id=issue.id,
            laptop_id=it["laptop_id"],
            student_full_name=(it.get("student_full_name") or "").strip(),
            student_group=(it.get("student_group") or "").strip(),
            condition=cond or None,
            has_mouse=bool(it.get("has_mouse")),
            has_charger=bool(it.get("has_charger")),
        ))
        laptop = laptops[it["laptop_id"]]
        laptop.status = STATUS_ISSUED
        # Если состояние указали — обновляем его и на самом ноутбуке,
        # чтобы столбец "Состояние" в таблице показывал актуальное значение.
        if cond:
            laptop.condition = cond

    db.session.commit()
    return jsonify(issue.to_dict()), 201


@api.post("/issues/<int:issue_id>/return")
def return_issue(issue_id):
    """Вернуть всю выдачу: закрываем все её активные позиции, освобождаем ноуты."""
    issue = db.session.get(Issue, issue_id)
    if issue is None:
        return jsonify({"error": "Выдача не найдена."}), 404

    now = utcnow()
    for item in issue.items:
        if item.returned_at is None:
            item.returned_at = now
            if item.laptop:
                item.laptop.status = STATUS_FREE
    issue.returned_at = now

    db.session.commit()
    return jsonify(issue.to_dict())


@api.post("/laptops/<int:laptop_id>/release")
def release_laptop(laptop_id):
    """Освободить один ноутбук (кнопка "Очистить" в таблице)."""
    laptop = db.session.get(Laptop, laptop_id)
    if laptop is None:
        return jsonify({"error": "Ноутбук не найден."}), 404

    item = laptop.active_item()
    if item is not None:
        item.returned_at = utcnow()
        # Если в выдаче не осталось активных позиций — закрываем и её.
        issue = item.issue
        if issue and all(i.returned_at is not None for i in issue.items):
            issue.returned_at = utcnow()

    laptop.status = STATUS_FREE
    db.session.commit()
    return jsonify(laptop.to_dict())


@api.get("/history")
def get_history():
    # Список выдач от свежих к старым (с вложенными позициями).
    rows = Issue.query.order_by(Issue.created_at.desc()).all()
    return jsonify([issue.to_dict() for issue in rows])
