from flask import Flask
from flask_cors import CORS

import os

from app.config import Config
from app.extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # CORS: разрешаем фронту обращаться к /api.
    # Локальные адреса Vite (host 127.0.0.1 — см. vite.config.js; 127.0.0.1 и
    # localhost для браузера РАЗНЫЕ, поэтому оба варианта). На бою адрес фронта
    # (например, https://имя.onrender.com) задаётся переменной FRONTEND_ORIGIN,
    # можно несколько через запятую — править код не нужно.
    origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]
    frontend_origin = os.getenv("FRONTEND_ORIGIN")
    if frontend_origin:
        origins.extend(o.strip() for o in frontend_origin.split(",") if o.strip())
    CORS(app, resources={r"/api/*": {"origins": origins}})

    # Импорт маршрутов внутри функции — чтобы избежать циклических импортов.
    from app.routes import api
    app.register_blueprint(api)

    # Создаём таблицы, если их ещё нет.
    with app.app_context():
        db.create_all()

    return app