import os
from dotenv import load_dotenv

# Загружаем переменные из файла .env (если он есть рядом).
# Почему так: строку подключения к БД нельзя хранить прямо в коде —
# там пароль. .env лежит локально и не попадает в git (см. .gitignore).
load_dotenv()


class Config:
    # Строка подключения к PostgreSQL.
    # Формат: postgresql://пользователь:пароль@хост:порт/имя_базы
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:postgres@localhost:5432/laptops_db",
    )

    # Отключаем лишнюю систему отслеживания изменений SQLAlchemy —
    # она ест память и для нас бесполезна. Это рекомендация самих авторов.
    SQLALCHEMY_TRACK_MODIFICATIONS = False
