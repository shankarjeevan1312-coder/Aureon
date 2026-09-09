# ===================================================
# AUREON Setup & Environment Preparation
# ===================================================

$ErrorActionPreference = "Stop"
Write-Host ">>> Initializing AUREON Environment..." -ForegroundColor Cyan

# Check for Python
$pythonCmd = Get-Command python.exe -ErrorAction SilentlyContinue
if (-not $pythonCmd) {
    # Check default user install location
    $userPython = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
    if (Test-Path $userPython) {
        $pythonPath = $userPython
    } else {
        Write-Host "Python not found. Attempting non-elevated user installation..." -ForegroundColor Yellow
        $installerUrl = "https://www.python.org/ftp/python/3.11.9/python-3.11.9-amd64.exe"
        $installerPath = "$env:TEMP\python-3.11.9-amd64.exe"
        Invoke-WebRequest -Uri $installerUrl -OutFile $installerPath
        Start-Process -FilePath $installerPath -ArgumentList "/quiet", "InstallAllUsers=0", "Include_pip=1", "PrependPath=1", "Include_launcher=0" -Wait
        $pythonPath = "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe"
    }
} else {
    $pythonPath = $pythonCmd.Source
}

Write-Host "Using Python: $pythonPath" -ForegroundColor Green

# Create Virtual Environment
$venvPath = Join-Path $PSScriptRoot ".venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment in .venv..." -ForegroundColor Cyan
    & $pythonPath -m venv $venvPath
}

$venvPython = Join-Path $venvPath "Scripts\python.exe"
$venvPip = Join-Path $venvPath "Scripts\pip.exe"

# Install Dependencies
Write-Host "Upgrading pip and installing requirements..." -ForegroundColor Cyan
& $venvPip install --upgrade pip
& $venvPip install -r (Join-Path $PSScriptRoot "requirements.txt")
& $venvPip install pytest pytest-asyncio

Write-Host "`n>>> AUREON setup completed successfully!" -ForegroundColor Green
Write-Host "Launch with: .\run.bat" -ForegroundColor Cyan
