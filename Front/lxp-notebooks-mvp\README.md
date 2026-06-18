# LXP Notebooks

MVP-модуль учета колледжных ноутбуков. Текущий старый макет можно оставить как визуальный референс, а эта папка показывает новую структуру под выбранный стек.

## Стек

- Frontend: Vue.js + Vite
- Backend: Python + Flask
- Database: PostgreSQL

## Структура

```text
backend/
  app/
    __init__.py
    config.py
    extensions.py
    models.py
    routes.py
  .env.example
  requirements.txt
  run.py
frontend/
  src/
    App.vue
    api.js
    main.js
    style.css
  index.html
  package.json
```

## Backend запуск

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
flask --app run.py db init
flask --app run.py db migrate -m "initial schema"
flask --app run.py db upgrade
python seed.py
python run.py
```

Перед запуском нужно создать PostgreSQL-базу `lxp_notebooks` или поменять `DATABASE_URL` в `.env`.

## Frontend запуск

```bash
cd frontend
npm install
npm run dev
```

По умолчанию frontend ожидает backend на `http://localhost:5000/api`.

## Быстрый запуск на Windows

Если нужен самый простой локальный запуск без PostgreSQL, используй bat-файлы из корня проекта:

```bat
start-backend.bat
start-frontend.bat
```

Или сразу оба:

```bat
start-project.bat
```

Этот быстрый режим запускает backend на временной SQLite-базе `dev.db`, чтобы можно было смотреть проект без отдельной настройки PostgreSQL.

## Основная backend-логика

- Преподаватель выбирает себя, аудиторию и название пары.
- В одной выдаче можно указать от 1 до 10 ноутбуков.
- Каждый ноутбук закрепляется за одним учеником.
- ФИО и группа ученика обязательны.
- Занятый ноутбук нельзя выдать повторно.
- В историю записывается выдача и возврат.
- История имеет поле `expires_at`, рассчитанное на 7 дней хранения.
