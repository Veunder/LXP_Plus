from datetime import date as date_type, time, datetime

from flask import Blueprint, request, jsonify
from sqlalchemy import or_

from extensions import db
from models import (
    Laptop, Teacher, History,
    ALLOWED_STATUSES, STATUS_FREE, STATUS_BUSY, STATUS_UNAVAILABLE,
)

# Все адреса под префиксом /api — фронтенд (Vue) обращается к /api/laptops и т.д.
api = Blueprint("api", __name__, url_prefix="/api")


def parse_time(value):
    # Время приходит строкой "14:30". Превращаем в объект time. None — если пусто.
    if not value:
        return None
    return time.fromisoformat(value)


def now_time():
    # Текущее время без микросекунд — для отметок начала/конца брони.
    return datetime.now().time().replace(microsecond=0)


# ---------- Справочник преподавателей (для выпадающего списка на фронте) ----------

@api.get("/teachers")
def list_teachers():
    teachers = Teacher.query.order_by(Teacher.lname, Teacher.fname).all()
    return jsonify([t.to_dict() for t in teachers])


# ---------- Ноутбуки: список и создание ----------

@api.get("/laptops")
def list_laptops():
    query = Laptop.query

    # Фильтр по статусу: /api/laptops?status=Свободен
    status = request.args.get("status")
    if status:
        query = query.filter(Laptop.status == status)

    # Фильтр по аудитории: /api/laptops?nclass=А-101
    nclass = request.args.get("nclass")
    if nclass:
        query = query.filter(Laptop.nclass == nclass)

    # Поиск по преподавателю или аудитории: /api/laptops?q=Смирнов
    # ilike — регистронезависимое совпадение. outerjoin, чтобы в выдачу
    # попадали и свободные ноутбуки (у них преподавателя нет).
    q = request.args.get("q")
    if q:
        like = f"%{q}%"
        query = query.outerjoin(Teacher, Laptop.id_pred == Teacher.id_pred).filter(
            or_(
                Laptop.nclass.ilike(like),
                Teacher.lname.ilike(like),
                Teacher.fname.ilike(like),
            )
        )

    laptops = query.order_by(Laptop.id_laptop).all()
    return jsonify([item.to_dict() for item in laptops])


@api.post("/laptops")
def create_laptop():
    data = request.get_json() or {}

    status = data.get("status", STATUS_FREE)
    if status not in ALLOWED_STATUSES:
        return jsonify({"error": f"недопустимый статус: {status}"}), 400

    laptop = Laptop(
        status=status,
        id_pred=data.get("id_pred"),
        id_stud=data.get("id_stud"),
        nclass=data.get("nclass"),
        mouse=bool(data.get("mouse", False)),
        charger=bool(data.get("charger", False)),
        condition=data.get("condition"),
    )
    db.session.add(laptop)
    db.session.commit()
    return jsonify(laptop.to_dict()), 201


# ---------- Ноутбуки: один, изменение, удаление ----------

@api.get("/laptops/<int:laptop_id>")
def get_laptop(laptop_id):
    laptop = db.session.get(Laptop, laptop_id)
    if laptop is None:
        return jsonify({"error": "ноутбук не найден"}), 404
    result = laptop.to_dict()
    # Заодно отдаём историю бронирований этого ноутбука.
    result["history"] = [rec.to_dict() for rec in laptop.history]
    return jsonify(result)


@api.put("/laptops/<int:laptop_id>")
def update_laptop(laptop_id):
    laptop = db.session.get(Laptop, laptop_id)
    if laptop is None:
        return jsonify({"error": "ноутбук не найден"}), 404

    data = request.get_json() or {}

    # Обновляем только присланные поля — частичный апдейт не затирает остальное.
    for field in ("id_pred", "id_stud", "nclass", "condition"):
        if field in data:
            setattr(laptop, field, data[field])
    for bool_field in ("mouse", "charger"):
        if bool_field in data:
            setattr(laptop, bool_field, bool(data[bool_field]))

    if "status" in data:
        if data["status"] not in ALLOWED_STATUSES:
            return jsonify({"error": f"недопустимый статус: {data['status']}"}), 400
        laptop.status = data["status"]

    db.session.commit()
    return jsonify(laptop.to_dict())


@api.delete("/laptops/<int:laptop_id>")
def delete_laptop(laptop_id):
    laptop = db.session.get(Laptop, laptop_id)
    if laptop is None:
        return jsonify({"error": "ноутбук не найден"}), 404
    db.session.delete(laptop)
    db.session.commit()
    return "", 204


# ---------- Бронирование (взять) и возврат ----------

@api.post("/laptops/<int:laptop_id>/book")
def book_laptop(laptop_id):
    """Взять ноутбук: создаём запись в истории и ставим статус 'Занят'."""
    laptop = db.session.get(Laptop, laptop_id)
    if laptop is None:
        return jsonify({"error": "ноутбук не найден"}), 404

    # Взять можно только свободный. 409 = состояние не позволяет операцию.
    if laptop.status != STATUS_FREE:
        return jsonify({
            "error": f"ноутбук нельзя взять, текущий статус: {laptop.status}"
        }), 409

    data = request.get_json() or {}
    id_pred = data.get("id_pred")
    id_stud = data.get("id_stud")
    if id_pred is None and id_stud is None:
        return jsonify({"error": "нужно указать id_pred или id_stud"}), 400

    # Если указан преподаватель — проверим, что он есть в справочнике.
    # Иначе PostgreSQL вернёт сырую ошибку внешнего ключа (некрасивый 500).
    if id_pred is not None and db.session.get(Teacher, id_pred) is None:
        return jsonify({"error": f"преподаватель id_pred={id_pred} не найден"}), 400

    record = History(
        id_laptop=laptop.id_laptop,
        id_pred=id_pred,
        id_stud=id_stud,
        date=date_type.today(),
        stime=parse_time(data.get("stime")) or now_time(),
        ftime=parse_time(data.get("ftime")),  # может быть пусто — закроется при возврате
        condition=data.get("condition"),
    )

    # Денормализованное "текущее" состояние ноутбука — чтобы в списке сразу
    # видеть, кто держит ноутбук, без обращения к истории (как в макете).
    laptop.status = STATUS_BUSY
    laptop.id_pred = id_pred
    laptop.id_stud = id_stud
    if "nclass" in data:
        laptop.nclass = data["nclass"]
    if "mouse" in data:
        laptop.mouse = bool(data["mouse"])
    if "charger" in data:
        laptop.charger = bool(data["charger"])

    # Создание записи и смена статуса — одной транзакцией: либо всё, либо ничего.
    db.session.add(record)
    db.session.commit()
    return jsonify(record.to_dict()), 201


@api.post("/laptops/<int:laptop_id>/return")
def return_laptop(laptop_id):
    """Вернуть ноутбук: закрываем активную бронь и ставим статус 'Свободен'."""
    laptop = db.session.get(Laptop, laptop_id)
    if laptop is None:
        return jsonify({"error": "ноутбук не найден"}), 404

    record = laptop.active_record()
    if record is None:
        return jsonify({"error": "у этого ноутбука нет активной брони"}), 409

    data = request.get_json() or {}
    record.ftime = now_time()
    if "condition" in data:
        record.condition = data["condition"]

    laptop.status = STATUS_FREE
    laptop.id_pred = None
    laptop.id_stud = None

    db.session.commit()
    return jsonify(record.to_dict())


# ---------- История и сводка для карточек ----------

@api.get("/history")
def list_history():
    # active=true вернёт только незакрытые брони (кто держит ноутбук сейчас).
    only_active = request.args.get("active") == "true"
    query = History.query
    if only_active:
        query = query.filter(History.ftime.is_(None))
    records = query.order_by(History.date.desc(), History.stime.desc()).all()
    return jsonify([rec.to_dict() for rec in records])


@api.get("/stats")
def stats():
    # Цифры для карточек сверху страницы: всего / свободны / заняты.
    return jsonify({
        "total": Laptop.query.count(),
        "free": Laptop.query.filter_by(status=STATUS_FREE).count(),
        "busy": Laptop.query.filter_by(status=STATUS_BUSY).count(),
        "unavailable": Laptop.query.filter_by(status=STATUS_UNAVAILABLE).count(),
    })
