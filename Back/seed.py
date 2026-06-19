"""Создаёт таблицы и наполняет базу демо-данными.

Запуск (из папки backend):  python seed.py

Данные подобраны под макет: 24 ноутбука, 6 заняты, из них 2 — у текущего
пользователя фронта (Фудулей М. С.), чтобы карточка "Мои бронирования" = 2.
"""
from datetime import timedelta

from app import create_app
from app.extensions import db
from app.models import (
    Teacher, Classroom, Laptop, Issue, IssueItem,
    STATUS_FREE, STATUS_ISSUED, utcnow,
)

app = create_app()

with app.app_context():
    db.drop_all()
    db.create_all()

    # ВАЖНО: фронт считает текущим пользователем преподавателя с полным именем
    # "Фудулей Мария Сергеевна" (это зашито в App.vue). Поэтому он обязательно
    # должен быть, иначе "Мои бронирования" не заработают.
    fudulei = Teacher(lname="Фудулей", fname="Мария", mname="Сергеевна", lesson="C#")
    smirnova = Teacher(lname="Смирнова", fname="А.", mname="В.", lesson="Математика")
    kozlov = Teacher(lname="Козлов", fname="И.", mname="П.", lesson="Информатика")
    petrova = Teacher(lname="Петрова", fname="М.", mname="С.", lesson="Физика")
    db.session.add_all([fudulei, smirnova, kozlov, petrova])

    rooms = {name: Classroom(name=name) for name in ("А-101", "А-205", "Б-204", "В-312")}
    db.session.add_all(rooms.values())

    # 24 ноутбука с номерами 1..24, изначально все свободны, состояние "Норма".
    laptops = [Laptop(number=n, status=STATUS_FREE, condition="Норма") for n in range(1, 25)]
    db.session.add_all(laptops)

    db.session.flush()  # проставляем id всем объектам перед созданием выдач

    now = utcnow()

    def make_issue(teacher, room, subject, rows):
        issue = Issue(
            teacher_id=teacher.id, classroom_id=room.id, subject_name=subject,
            created_at=now, expires_at=now + timedelta(days=7),
        )
        db.session.add(issue)
        db.session.flush()
        for laptop, fio, group, condition, mouse, charger in rows:
            db.session.add(IssueItem(
                issue_id=issue.id, laptop_id=laptop.id,
                student_full_name=fio, student_group=group,
                condition=condition, has_mouse=mouse, has_charger=charger,
            ))
            laptop.status = STATUS_ISSUED
            if condition:
                laptop.condition = condition

    # laptops[n] имеет number = n+1, т.е. laptops[6] -> NB-007.
    make_issue(smirnova, rooms["А-101"], "Математический анализ", [
        (laptops[6], "Орлов П. К.", "ИС-21", "Норма", False, True),
        (laptops[11], "Белова Н. А.", "ИС-21", "Царапина на крышке", False, False),
    ])
    make_issue(kozlov, rooms["Б-204"], "Основы программирования", [
        (laptops[20], "Гусев Р. Д.", "ПО-22", "Норма", True, True),
    ])
    make_issue(petrova, rooms["В-312"], "Физика", [
        (laptops[14], "Зайцева Л. М.", "ЭЛ-20", "Не работает тачпад", False, True),
    ])
    make_issue(fudulei, rooms["А-205"], "Базы данных", [
        (laptops[2], "Соколов А. А.", "ПО-22", "Норма", True, True),
        (laptops[8], "Морозова Е. В.", "ПО-22", "Норма", True, False),
    ])

    db.session.commit()

    busy = Laptop.query.filter_by(status=STATUS_ISSUED).count()
    print(f"Готово. Преподавателей: 4, аудиторий: {len(rooms)}, "
          f"ноутбуков: {len(laptops)} (занято {busy}, свободно {len(laptops) - busy}).")
