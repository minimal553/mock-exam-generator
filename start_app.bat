@echo off
setlocal
cd /d %~dp0
set APP_URL=http://127.0.0.1:18765
set APP_PORT=18765

echo [0/3] Stopping old app processes on port %APP_PORT% ...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr :%APP_PORT% ^| findstr LISTENING') do (
  taskkill /PID %%p /F >nul 2>nul
)
timeout /t 1 /nobreak >nul

if not exist .venv (
  echo [1/3] Creating virtual environment...
  python -m venv .venv
)

echo [2/3] Installing dependencies...
call .venv\Scripts\python -m pip install --upgrade pip >nul
if errorlevel 1 exit /b 1
call .venv\Scripts\python -m pip install -r standalone_app\requirements.txt
if errorlevel 1 exit /b 1

echo [3/3] Starting app at %APP_URL% ...
start "Gongkao Learning App Server" /D "%CD%" "%CD%\.venv\Scripts\python.exe" -m standalone_app.app
timeout /t 2 /nobreak >nul
start "" %APP_URL%
endlocal
