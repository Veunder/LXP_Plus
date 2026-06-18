@echo off
setlocal

cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
  echo Creating virtual environment...
  python -m venv .venv
)

call ".venv\Scripts\activate.bat"

echo Installing backend dependencies...
python -m pip install Flask==3.0.3 Flask-SQLAlchemy==3.1.1 Flask-Migrate==4.0.7 Flask-Cors==4.0.1 python-dotenv==1.0.1

set DATABASE_URL=sqlite:///dev.db

echo Preparing database...
python -c "from app import create_app; from app.extensions import db; app=create_app(); app.app_context().push(); db.create_all(); print('tables created')"
python seed.py

echo Starting backend on http://127.0.0.1:5000
python run.py
