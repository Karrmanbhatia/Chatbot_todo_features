@echo off
setlocal enabledelayedexpansion

REM Define backup directory
set "BACKUP_DIR=%~dp0backup"

REM Create backup directory if it doesn't exist
if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%"
    echo Created backup directory at %BACKUP_DIR%
)

REM Create a temporary file with paths to move (one per line)
set "TMP_LIST=%TEMP%\to_move_list.txt"
> "%TMP_LIST%" (
    echo rasa\Rasa_chatbot
    echo rasa\Dockerfile
    echo direct_script_runner.log
    echo filtered_errors.json
    echo test_output.json
    echo test_cdcarm_function.py
    echo generate_structure.py
    echo README for Ansys DiscoveryGPT.docx
    echo ~$ADME for Ansys DiscoveryGPT.docx
    echo gpt_neo_integration.py
    echo .rasa
)

REM Loop through each path safely
for /f "usebackq delims=" %%I in ("%TMP_LIST%") do (
    if exist "%%I" (
        echo Moving "%%I" to backup...
        move /Y "%%I" "%BACKUP_DIR%\" >nul
    ) else (
        echo Skipping "%%I" (not found)
    )
)

del "%TMP_LIST%"

echo.
echo ✅ Cleanup complete. All unneeded items moved to: %BACKUP_DIR%
pause
