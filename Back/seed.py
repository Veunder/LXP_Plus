"""Создаёт таблицы и наполняет базу тестовыми данными.

Запуск:  python seed.py
"""
from app import create_app
from extensions import db
from models import Teacher, Laptop, STATUS_FREE, STATUS_UNAVAILABLE

app = create_app()

with app.app_context():
    # drop_all + create_all пересоздаёт схему с нуля. Удобно, пока структура
    # меняется. ВНИМАНИЕ: стирает данные — в зрелом проекте берут миграции.
    db.drop_all()
    db.create_all()

    # Сначала преподаватели — на них ссылаются ноутбуки.
    teachers = [
        Teacher(lname="Смирнова", fname="Анна", mname="Викторовна"),
        Teacher(lname="Козлов", fname="Иван", mname="Петрович"),
    ]
    db.session.add_all(teachers)
    # flush отправляет данные в БД и проставляет id_pred, но НЕ завершает
    # транзакцию — нужно, чтобы ниже сослаться на этих преподавателей.
    db.session.flush()

    # Свободные ноутбуки оставляем без преподавателя (id_pred = None),
    # как в макете: у свободных в колонке "Преподаватель" стоит прочерк.
    laptops = [
        Laptop(status=STATUS_FREE, nclass="А-101",
               mouse=True, charger=True, condition="Норма"),
        Laptop(status=STATUS_FREE, nclass="Б-204",
               mouse=False, charger=True, condition="Норма"),
        Laptop(status=STATUS_UNAVAILABLE, nclass="В-312",
               mouse=True, charger=False, condition="В ремонте"),
    ]
    db.session.add_all(laptops)
    db.session.commit()

    print(f"Готово: преподавателей — {len(teachers)}, ноутбуков — {len(laptops)}")
