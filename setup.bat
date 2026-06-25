@echo off
setlocal enabledelayedexpansion

echo ==============================================
echo       MercariBuddy Discord Bot Setup
echo ==============================================
echo.

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ from https://www.python.org/
    echo Make sure to check the box "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Get python version
for /f "tokens=2" %%i in ('python --version') do set pyver=%%i
echo [INFO] Found Python version !pyver!

:: 2. Create Virtual Environment
if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo [INFO] Virtual environment created successfully.
) else (
    echo [INFO] Virtual environment already exists.
)

:: 3. Activate Virtual Environment and Install Requirements
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo [ERROR] Failed to activate virtual environment.
    pause
    exit /b 1
)

echo [INFO] Upgrading pip...
python -m pip install --upgrade pip

echo [INFO] Installing required libraries...
python -m pip install -r requirements.txt
if !errorlevel! neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)
echo [INFO] Dependencies installed successfully.

:: 4. Setup .env file
if not exist ".env" (
    echo [INFO] Creating default .env configuration file...
    
    :: Save current console code page
    for /f "tokens=4" %%a in ('chcp') do set oldcp=%%a
    
    :: Switch console code page to UTF-8
    chcp 65001 >nul
    
    :: Write .env file
    echo # Discord Bot Token - Get this from https://discord.com/developers/applications > .env
    echo DISCORD_TOKEN="" >> .env
    echo. >> .env
    echo # Database Configuration >> .env
    echo DB_TYPE="sqlite" >> .env
    echo USERNAME="" >> .env
    echo DATABASE="" >> .env
    echo PASSWORD="" >> .env
    echo HOST="" >> .env
    echo PORT="" >> .env
    
    :: Restore old console code page
    chcp !oldcp! >nul
    
    echo [INFO] .env file created. Please open it and add your DISCORD_TOKEN.
) else (
    echo [INFO] .env file already exists.
)

echo.
echo ==============================================
echo Setup Complete!
echo 1. Open and configure your .env file with your Discord Bot Token.
echo 2. Run 'run.bat' to start the bot.
echo ==============================================
echo.
pause
