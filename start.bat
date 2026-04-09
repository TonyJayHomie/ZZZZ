@echo off
title Claude Web Wrapper
echo ============================================================
echo   Claude Web Wrapper
echo   OpenAI-compatible API via DOM automation
echo   Zero credentials — pure browser automation
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

:: Check for --headed flag
set ARGS=
if "%1"=="--headed" (
    set ARGS=--headed
    echo [MODE] Running in HEADED mode — browser window will open for login
) else (
    echo [MODE] Running in HEADLESS mode
)

echo [START] Starting server on port 3967...
echo [START] API: http://127.0.0.1:3967/v1/chat/completions
echo [START] Models: http://127.0.0.1:3967/v1/models
echo.

python main.py --port 3967 %ARGS% %*

pause
