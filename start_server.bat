@echo off
REM Flight Departure Tracking System - Startup Script for Windows

echo ========================================
echo Flight Departure Tracking System
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed
    pause
    exit /b 1
)

echo Setting up temporary virtual environment...

REM Create temporary virtual environment
set VENV_DIR=.venv_temp

REM Remove old venv if it exists
if exist "%VENV_DIR%" (
    rmdir /s /q "%VENV_DIR%"
)

REM Create new virtual environment
python -m venv "%VENV_DIR%"

REM Activate virtual environment
call "%VENV_DIR%\Scripts\activate.bat"

echo Installing Flask and requests in virtual environment...
pip install --quiet flask requests

echo.
echo ========================================
echo Server Starting...
echo ========================================
echo ATC Password: atc2024
echo Pilot Interface: http://localhost:5000/
echo ATC Interface: http://localhost:5000/atc
echo ========================================
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the server
python server.py

REM Cleanup on exit
echo.
echo Cleaning up temporary virtual environment...
call "%VENV_DIR%\Scripts\deactivate.bat"
rmdir /s /q "%VENV_DIR%"
echo Done!
pause
