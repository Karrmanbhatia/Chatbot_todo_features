@echo off
title TFIA: Start Web & Flask Servers

REM === Start Flask Backend Server ===
start "Flask Server" cmd /k "cd /d D:\AI_project\ARM_AI\TFIA_WEB\Chatbot_todo_features\actions && py flask_app.py"

REM === Start Frontend HTTP Server ===
start "Frontend Server" cmd /k "cd /d D:\AI_project\ARM_AI\TFIA_WEB\Chatbot_todo_features\web && py -m http.server 8000"

echo Both servers started in separate terminals.
