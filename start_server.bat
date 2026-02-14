@echo off

echo ========================================
echo Flight Departure Tracking System
echo ========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed
    pause
    exit /b 1
)

echo Setting up temporary virtual environment...

set VENV_DIR=.venv_temp

if exist "%VENV_DIR%" (
    rmdir /s /q "%VENV_DIR%"
)

python -m venv "%VENV_DIR%"

call "%VENV_DIR%\Scripts\activate.bat"

echo Installing Flask in virtual environment...
pip install --quiet flask

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

python server.py

echo.
echo Cleaning up temporary virtual environment...
call "%VENV_DIR%\Scripts\deactivate.bat"
rmdir /s /q "%VENV_DIR%"
echo Done!
pause
