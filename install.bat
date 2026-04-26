@echo off
title SAAS KILLER - INSTALLER
echo ===================================================
echo   [🐺] WENDIGO : SAAS KILLER INSTALLATION
echo ===================================================
echo.
echo [*] Creating isolated Python environment...
python -m venv harvester_venv

echo [*] Activating environment and installing dependencies...
call harvester_venv\Scripts\activate.bat
pip install -r requirements.txt
pip install fastapi uvicorn requests python-multipart

echo.
echo [✅] INSTALLATION COMPLETE!
echo You can now double-click "start_web_shell.bat" to launch the UI.
pause
