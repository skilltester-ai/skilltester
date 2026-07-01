@echo off
setlocal EnableExtensions

cd /d "%~dp0"

set "APP_NAME=Harn-LLM Tester"
set "VENV_DIR=.venv"
set "BOOTSTRAP_DIR=.runtime\bootstrap"
set "MARKER_FILE=%BOOTSTRAP_DIR%\deps-installed"
set "REQUIREMENTS_FILE=requirements.txt"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"

echo ========================================
echo   Starting %APP_NAME%
echo ========================================

set "RUNTIME_READY=0"
if exist "%VENV_PYTHON%" if exist "%MARKER_FILE%" set "RUNTIME_READY=1"

if "%RUNTIME_READY%"=="1" (
    echo Using existing local runtime.
) else (
    set "CREATED_VENV=0"

    if not exist "%VENV_PYTHON%" (
        echo Creating local Python environment...
        call :create_venv
        if errorlevel 1 goto fail
        set "CREATED_VENV=1"
    )

    echo Installing Python dependencies...
    if not exist "%BOOTSTRAP_DIR%" mkdir "%BOOTSTRAP_DIR%"
    "%VENV_PYTHON%" -m pip install --upgrade pip
    if errorlevel 1 goto fail
    "%VENV_PYTHON%" -m pip install -r "%REQUIREMENTS_FILE%"
    if errorlevel 1 goto fail
    echo installed>"%MARKER_FILE%"
)

echo.
echo Opening %APP_NAME%...
"%VENV_PYTHON%" start.py --platform windows
if errorlevel 1 goto fail
goto done

:create_venv
where py >nul 2>nul
if not errorlevel 1 (
    py -3 -m venv "%VENV_DIR%"
    exit /b %ERRORLEVEL%
)
where python >nul 2>nul
if not errorlevel 1 (
    python -m venv "%VENV_DIR%"
    exit /b %ERRORLEVEL%
)
echo Python 3 was not found. Install Python 3 and run this script again.
exit /b 1

:fail
echo.
echo %APP_NAME% startup failed.
pause
exit /b 1

:done
endlocal
