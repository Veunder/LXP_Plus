from flask import Flask
from flask_cors import CORS

from config import Config
from extensions import db


def create_app():
    # Паттерн "фабрика приложения": создание app завёрнуто в функцию.
    # Почему так: позволяет создавать отдельный экземпляр под тесты,
    # и убирает проблемы с порядком импортов. Стандарт для Flask-проектов.
    app = Flask(__name__)
    app.config.from_object(Config)

    # Подключаем базу к приложению. db.init_app, а не SQLAlchemy(app),
    # потому что объект db мы создали заранее в extensions.py.
    db.init_app(app)

    # CORS разрешает фронтенду обращаться к API.
    # Почему это нужно: Vue на этапе разработки крутится на своём порту
    # (например, http://localhost:5173), а Flask — на http://localhost:5000.
    # Это разные origin, и браузер по умолчанию блокирует такие запросы.
    # Здесь разрешаем только адреса /api/* и типичные адреса Vite/Vue.
    CORS(app, resources={r"/api/*": {"origins": [
        "http://localhost:5173",
        "http://localhost:8080",
    ]}})

    # Регистрируем маршруты. Импорт внутри функции — снова чтобы не ловить
    # циклические импорты (routes импортирует models, models импортирует db).
    from routes import api
    app.register_blueprint(api)

    return app


app = create_app()


if __name__ == "__main__":
    # Запуск для разработки: python app.py
    # debug=True даёт автоперезагрузку и подробные ошибки. В продакшене выключить.
    app.run(debug=True, port=5000)
