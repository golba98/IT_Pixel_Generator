@echo off
setlocal
:: Ensure we are in the script's directory even if run from elsewhere
cd /d "%~dp0"

:: Set path to the virtual environment's python
set "VENV_PYTHON=%~dp0.venv\Scripts\python.exe"

:: Check if the virtual environment's python exists
if exist "%VENV_PYTHON%" (
    echo [INFO] Virtual environment found. Starting GUI...
    "%VENV_PYTHON%" gui_converter.py
) else (
    echo [WARNING] Virtual environment not found at: "%VENV_PYTHON%"
    echo [INFO] Trying system 'python' instead...
    python gui_converter.py
)

:: If there was an error, keep the window open so we can read it
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] The program failed with exit code %ERRORLEVEL%.
    echo Please ensure Python is installed and requirements are installed.
    pause
)
endlocal
