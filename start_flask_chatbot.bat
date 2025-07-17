@echo off
REM === Navigate to the Flask app directory relative to the .bat file ===
cd /d "%~dp0actions"

REM === Find VPN IP address ===
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R /C:"IPv4 Address"') do (
    set ip=%%a
    goto :next
)
:next
set ip=%ip:~1%

REM === Display Flask launch info ===
echo ====================================================
echo Running Flask app from relative path: actions\flask_app.py
echo Your server will be accessible at: http://%ip%:5000/
echo ====================================================

REM === Open the browser to the app ===
start http://%ip%:5000/

REM === Run the Flask server ===
py flask_app.py

pause
