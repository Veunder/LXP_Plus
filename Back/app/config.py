import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Строка подключения к PostgreSQL. Берётся из .env (см. .env.example).
    # Формат: postgresql://пользователь:пароль@хост:порт/имя_базы
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres@localhost:5432/lxplaptops_db",
    )

    # Отключаем лишнюю систему отслеживания изменений — экономит память.
    SQLALCHEMY_TRACK_MODIFICATIONS = False