@echo off
REM Start the Transactions API: creates/activates a venv, installs
REM dependencies, then runs the server with auto-reload.
REM
REM Usage:
REM   run.bat            (starts on port 8000)
REM   run.bat 8080       (starts on a custom port)

setlocal

set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%.."

if not exist venv (
    echo Creating virtual environment in venv ...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing dependencies ...
pip install -q -r requirements.txt

set "PORT=8000"
if not "%~1"=="" set "PORT=%~1"

echo.
echo Starting Transactions API on http://127.0.0.1:%PORT%
echo Docs (Swagger UI): http://127.0.0.1:%PORT%/docs
echo Press Ctrl+C to stop.
echo.

uvicorn src.app:app --reload --port %PORT%

endlocal
