@echo off
echo ==============================================
echo       Starting MercariBuddy Discord Bot
echo ==============================================
echo.

if not exist "venv\Scripts\activate.bat" (
    echo [ERROR] Virtual environment (venv) not found.
    echo Please run 'setup.bat' first to install requirements.
    echo.
    pause
    exit /b 1
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

if not exist ".env" (
    echo [ERROR] .env file not found.
    echo Please run 'setup.bat' first, or create a .env file.
    echo.
    pause
    exit /b 1
)

echo [INFO] Starting the bot...
python src/bot.py
if %errorlevel% neq 0 (
    echo [ERROR] The bot crashed or stopped with exit code %errorlevel%.
)
echo.
pause
