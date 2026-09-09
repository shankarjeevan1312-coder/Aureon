@echo off
setlocal
echo ===================================================
echo   AUREON — Operating Intelligence Launcher
echo ===================================================

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXEC=%~dp0.venv\Scripts\python.exe"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXEC=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
) else (
    set "PYTHON_EXEC=python"
)

echo Starting AUREON Backend on http://localhost:8000 ...
"%PYTHON_EXEC%" -m uvicorn aureon.server.api:app --host 0.0.0.0 --port 8000 --reload
pause
