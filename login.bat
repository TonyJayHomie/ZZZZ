@echo off
title Claude Web Wrapper — LOGIN
echo ============================================================
echo   Claude Web Wrapper — FIRST TIME LOGIN
echo   A browser window will open. Log into claude.ai.
echo   After login, close this and run start.bat
echo ============================================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

:: Check if venv exists, create if not
if not exist "venv" (
    echo [SETUP] Creating virtual environment...
    python -m venv venv
    echo [SETUP] Installing dependencies...
    call venv\Scripts\activate.bat
    pip install -r requirements.txt
    playwright install chromium
    echo.
    echo [SETUP] Setup complete!
    echo.
) else (
    call venv\Scripts\activate.bat
)

echo [LOGIN] Opening browser — log into claude.ai...
echo [LOGIN] After login, close this window and run start.bat
echo.

python main.py --login --port 3967

pause
