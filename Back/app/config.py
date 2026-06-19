import os
from dotenv import load_dotenv

load_dotenv()


def _normalize_db_url(url):
    # Некоторые хостинги (в т.ч. Render) выдают строку, начинающуюся с
    # "postgres://", а SQLAlchemy требует "postgresql://". Чиним автоматически.
    if url and url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql://", 1)
    return url


class Config:
    # Строка подключения к PostgreSQL. Берётся из .env (см. .env.example).
    # Формат: postgresql://пользователь:пароль@хост:порт/имя_базы
    SQLALCHEMY_DATABASE_URI = _normalize_db_url(
        os.getenv("DATABASE_URL")
        or "postgresql://postgres:postgres@localhost:5432/lxplaptops_db"
    )

    # Отключаем лишнюю систему отслеживания изменений — экономит память.
    SQLALCHEMY_TRACK_MODIFICATIONS = False