@echo off
setlocal enabledelayedexpansion

REM Move to the directory of this script
cd /d "%~dp0"

echo.
echo ==== Checking Python version ====
py --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH.
    pause
    exit /b 1
)

echo.
echo ==== Updating pip, setuptools, wheel ====
py -m pip install --upgrade pip setuptools wheel

echo.
if exist requirements.txt (
    echo ==== Installing dependencies from requirements.txt ====
    py -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
    echo ✅ Dependencies installed successfully.
) else (
    echo [WARN] requirements.txt not found. Skipping dependency installation.
)

pause
