@echo off
setlocal
echo Launching AUREON Desktop Window Application...

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXEC=%~dp0.venv\Scripts\python.exe"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXEC=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
) else (
    set "PYTHON_EXEC=python"
)

"%PYTHON_EXEC%" -m aureon.desktop
