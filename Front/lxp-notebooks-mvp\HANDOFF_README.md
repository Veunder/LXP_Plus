LXP Notebooks MVP Handoff

This package is prepared for transfer to another developer.

Project stack:
- Frontend: Vue.js + Vite
- Backend: Python + Flask
- Target database: PostgreSQL

What is inside:
- `frontend/` - current UI and client logic
- `backend/` - API, models, business rules
- `start-backend.bat` - local backend start with temporary SQLite
- `start-frontend.bat` - local frontend start
- `start-project.bat` - starts both parts on Windows

Quick local run without PostgreSQL

1. Open the project folder.
2. Run `start-project.bat`.
3. Wait until two console windows open.
4. Open `http://127.0.0.1:5173`.

In this mode:
- backend runs on temporary SQLite
- frontend runs through Vite
- test data is created automatically

Main URLs:
- Frontend: `http://127.0.0.1:5173`
- Backend health check: `http://127.0.0.1:5000/api/health`

What the database developer needs

1. Read `DB_INTEGRATION.md`.
2. Use `backend/app/models.py` as the source of truth for the schema.
3. Replace temporary SQLite usage with PostgreSQL through `DATABASE_URL`.
4. Keep current API contracts from `backend/app/routes.py`.

Important business rules already implemented

- Only a teacher issues laptops.
- One issue may contain from 1 to 10 laptops.
- One student from one group may have only one active laptop.
- The same laptop cannot be assigned twice in one request.
- Only free laptops can be issued.
- Mouse and charger flags are stored per issued laptop.
- History stores issue/return events for 7 days.
- A laptop can be manually released from the table UI.

Recommended handoff

Send the archive together with a short note:
- current project status
- which developer will connect PostgreSQL
- whether they should keep SQLite quick start for demo mode

