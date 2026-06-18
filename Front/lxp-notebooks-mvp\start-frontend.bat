@echo off
setlocal

cd /d "%~dp0frontend"

echo Installing frontend dependencies...
call npm.cmd install

echo Starting frontend on http://127.0.0.1:5173
call npm.cmd run dev
