@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   AUREON — Standalone Windows Executable Packager
echo ===================================================

if exist "%~dp0.venv\Scripts\python.exe" (
    set "PYTHON_EXEC=%~dp0.venv\Scripts\python.exe"
    set "PIP_EXEC=%~dp0.venv\Scripts\pip.exe"
) else (
    set "PYTHON_EXEC=python"
    set "PIP_EXEC=pip"
)

echo Installing PyInstaller...
"%PIP_EXEC%" install pyinstaller

echo Compiling AUREON Standalone Executable...
"%PYTHON_EXEC%" -m PyInstaller ^
    --name "Aureon" ^
    --noconfirm ^
    --onedir ^
    --windowed ^
    --add-data "aureon\server\static;aureon\server\static" ^
    --hidden-import "uvicorn" ^
    --hidden-import "uvicorn.logging" ^
    --hidden-import "uvicorn.loops" ^
    --hidden-import "uvicorn.loops.auto" ^
    --hidden-import "uvicorn.protocols" ^
    --hidden-import "uvicorn.protocols.http" ^
    --hidden-import "uvicorn.protocols.http.auto" ^
    --hidden-import "uvicorn.protocols.websockets" ^
    --hidden-import "uvicorn.protocols.websockets.auto" ^
    --hidden-import "uvicorn.lifespan" ^
    --hidden-import "uvicorn.lifespan.on" ^
    --hidden-import "fastapi" ^
    --hidden-import "starlette" ^
    --hidden-import "websockets" ^
    --hidden-import "edge_tts" ^
    --hidden-import "psutil" ^
    aureon\desktop.py

echo.
echo ===================================================
echo   Build complete! Output located at: dist\Aureon\
echo ===================================================
pause
