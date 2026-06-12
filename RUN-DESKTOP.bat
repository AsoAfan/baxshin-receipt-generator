@echo off
echo Starting Receipt App in Desktop Mode...
cd /d "%~dp0"
if exist venv\Scripts\python.exe (
    venv\Scripts\python.exe desktop_app_gui.py
) else (
    python desktop_app_gui.py
)
pause
