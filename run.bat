@echo off
title Lineage W Chat Capture - Startup Script
echo ===================================================
echo   Lineage W Chat Capture - Startup Script
echo ===================================================
echo.

cd /d "%~dp0"

:: If venv already exists, jump directly to activating it
if exist "venv" goto :start_app

echo [INFO] First time startup. Searching for base Python...
set "BASE_PYTHON="

if exist "..\lineage-w-controller\venv\Scripts\python.exe" (
    set "BASE_PYTHON=..\lineage-w-controller\venv\Scripts\python.exe"
    echo [INFO] Found adjacent lineage-w-controller python environment.
    goto :create_venv
)

if exist "..\realtime-stt\venv\Scripts\python.exe" (
    set "BASE_PYTHON=..\realtime-stt\venv\Scripts\python.exe"
    echo [INFO] Found adjacent STT venv python environment.
    goto :create_venv
)

if exist "..\realtime-stt\runtime\python.exe" (
    set "BASE_PYTHON=..\realtime-stt\runtime\python.exe"
    echo [INFO] Found adjacent STT portable python environment.
    goto :create_venv
)

python --version >nul 2>&1
if not errorlevel 1 (
    set "BASE_PYTHON=python"
    echo [INFO] Using system python.
    goto :create_venv
)

echo [ERROR] No Python executable found!
echo Please make sure Python 3.10+ is installed and added to PATH.
pause
exit /b 1

:create_venv
echo [INFO] Creating virtual environment (venv)...
"%BASE_PYTHON%" -m venv venv
if errorlevel 1 (
    echo [ERROR] Failed to create virtual environment!
    pause
    exit /b 1
)
echo [INFO] Virtual environment created successfully.

:start_app
:: Activate venv and install dependencies
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Checking and installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies. Please check network connection.
    pause
    exit /b 1
)
echo [INFO] Dependencies checked and installed successfully.

echo [INFO] Starting application...
python main.py
if errorlevel 1 (
    echo [ERROR] Application exited abnormally.
    pause
)

exit /b
