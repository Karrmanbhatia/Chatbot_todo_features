@echo off
setlocal

REM Detect current working directory
set "ROOT_DIR=%~dp0"
cd /d "%ROOT_DIR%"

REM Step 1: Install Python dependencies
echo Installing Python dependencies...
cd actions
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies.
    pause
    exit /b 1
)

REM Step 2: Start Flask backend in new terminal
echo Starting Flask backend...
start cmd /k "cd /d %ROOT_DIR%actions && py flask_app.py"

REM Step 3: Start frontend static server in another terminal
echo Starting frontend on http://localhost:8000...
start cmd /k "cd /d %ROOT_DIR%web && py -m http.server 8000"

echo All services started successfully.
pause

