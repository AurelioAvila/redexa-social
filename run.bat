@echo off
cd /d "%~dp0"
if not exist venv (
    python -m venv venv
    call venv\Scripts\python -m pip install --upgrade "pip>=26.2"
    if errorlevel 1 exit /b 1
    call venv\Scripts\python -m pip install -r requirements.txt
    if errorlevel 1 exit /b 1
)
call venv\Scripts\python app.py
echo.
echo The server has stopped. Press any key to close.
pause >nul
