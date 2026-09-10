@echo off
setlocal
echo ===================================================
echo   AUREON ? Autonomous Voice Daemon (Siri Style)
echo   Wake Word: "Hey Aureon" or "Aureon"
echo   Dismiss:   "Proceed Aureon" or "Stop"
echo ===================================================

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXEC=%~dp0.venv\Scripts\python.exe"
) else (
    set "PYTHON_EXEC=python"
)

echo Starting Background Voice Assistant...
"%PYTHON_EXEC%" aureon\daemon.py
pause
