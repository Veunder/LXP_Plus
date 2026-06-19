from flask import Flask
from flask_cors import CORS

from app.config import Config
from app.extensions import db


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # CORS: разрешаем фронту (Vite на порту 5173) обращаться к /api.
    # ВАЖНО: фронт у нас поднимается на host 127.0.0.1 (см. vite.config.js),
    # а 127.0.0.1 и localhost для браузера — РАЗНЫЕ адреса, поэтому в списке
    # должны быть оба варианта, иначе запросы молча заблокируются.
    CORS(app, resources={r"/api/*": {"origins": [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ]}})

    # Импорт маршрутов внутри функции — чтобы избежать циклических импортов.
    from app.routes import api
    app.register_blueprint(api)

    # Создаём таблицы, если их ещё нет (для SQLite-старта это удобно).
    with app.app_context():
        db.create_all()

    return app
