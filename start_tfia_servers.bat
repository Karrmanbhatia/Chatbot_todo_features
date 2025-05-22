@echo off
setlocal enabledelayedexpansion

REM Move to the directory of this script
cd /d "%~dp0"

echo 🔧 Checking Python version...
py --version || (
    echo ❌ Python is not installed or not in PATH.
    pause
    exit /b 1
)

REM Update pip, setuptools, wheel (best effort)
echo 🔄 Updating pip, setuptools, wheel...
py -m pip install --upgrade pip setuptools wheel

REM Check and install dependencies
if exist requirements.txt (
    echo 📦 Installing dependencies from requirements.txt...
    py -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ Failed to install dependencies.
        pause
        exit /b 1
    )
) else (
    echo ⚠️ requirements.txt not found. Skipping dependency installation.
)

REM Start Flask backend
echo 🚀 Launching Flask backend...
start "" cmd /k "cd actions && py flask_app.py"

REM Start frontend static server
echo 🌐 Launching frontend at http://localhost:8000 ...
start "" cmd /k "cd web && py -m http.server 8000"

echo ✅ All services started. You can now interact via the browser.
pause
