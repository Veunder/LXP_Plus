@echo off
setlocal

cd /d "%~dp0"

start "LXP Backend" cmd /k "%~dp0start-backend.bat"
start "LXP Frontend" cmd /k "%~dp0start-frontend.bat"

echo Project windows opened:
echo Backend:  http://127.0.0.1:5000/api/health
echo Frontend: http://127.0.0.1:5173
