@echo off
title SAAS KILLER - WEB SHELL
echo ===================================================
echo   [🐺] WENDIGO : IGNITING DUAL-PLANE ENGINE
echo ===================================================
echo.
echo [*] Starting API and Compute Nodes...
call harvester_venv\Scripts\activate.bat
python serve.py
pause
