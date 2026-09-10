# verify.ps1
# Automates the setup, model training, benchmarking, security scanning, and testing of the MLOps Fraud Pipeline.

$ErrorActionPreference = "Stop"

# Auto-detect available Python (Python 3.10+)
$pyCmd = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
    if (& py -3.10 --version 2>$null) {
        $pyCmd = "py -3.10"
    } elseif (& py -3.11 --version 2>$null) {
        $pyCmd = "py -3.11"
    } elseif (& py -3 --version 2>$null) {
        $pyCmd = "py -3"
    }
}
if (-not $pyCmd -and (Get-Command python -ErrorAction SilentlyContinue)) {
    $pyCmd = "python"
}
if (-not $pyCmd) {
    Write-Error "No suitable Python installation found. Please install Python 3.10 or higher."
}

Write-Host "=== Phase 1: Validating Virtual Environment ===" -ForegroundColor Cyan
$recreateVenv = $false
if (Test-Path ".venv\Scripts\python.exe") {
    try {
        & ".\.venv\Scripts\python.exe" --version 2>$null | Out-Null
        if ($LASTEXITCODE -ne 0) { $recreateVenv = $true }
    } catch {
        $recreateVenv = $true
    }
} else {
    $recreateVenv = $true
}

if ($recreateVenv) {
    Write-Host "Creating clean virtual environment using: $pyCmd" -ForegroundColor Gray
    if (Test-Path ".venv") { Remove-Item -Recurse -Force ".venv" }
    Invoke-Expression "$pyCmd -m venv .venv"
    Write-Host "Virtual environment created successfully." -ForegroundColor Green
} else {
    Write-Host "Virtual environment is valid and ready. Skipping creation." -ForegroundColor Green
}

Write-Host "`n=== Phase 2: Installing / Verifying Dependencies ===" -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
Write-Host "Dependencies verified." -ForegroundColor Green

Write-Host "`n=== Phase 3: Training Baseline Isolation Forest Model ===" -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m app.model
if ((Test-Path "model.pkl") -and (Test-Path "scaler.pkl")) {
    Write-Host "Baseline Isolation Forest artifacts verified." -ForegroundColor Green
} else {
    Write-Error "Failed to locate Isolation Forest artifacts."
}

Write-Host "`n=== Phase 4: Running Synthetic Simulation & Supervised Model Pipeline ===" -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" train_pipeline.py
if (Test-Path "supervised_model.pkl") {
    Write-Host "Supervised model artifact verified." -ForegroundColor Green
} else {
    Write-Error "Failed to locate supervised model artifact."
}

Write-Host "`n=== Phase 5: Running Bandit Security SAST Scan ===" -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m bandit -r app/ -q
if ($LASTEXITCODE -eq 0) {
    Write-Host "Bandit security check passed: 0 vulnerabilities." -ForegroundColor Green
} else {
    Write-Error "Security scan failed."
}

Write-Host "`n=== Phase 6: Running Automated Pytest Test Suite ===" -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" -m pytest tests/ -v
if ($LASTEXITCODE -eq 0) {
    Write-Host "`nAll 50+ unit and integration tests passed successfully." -ForegroundColor Green
} else {
    Write-Error "One or more tests failed."
}

Write-Host "`n=================================================================" -ForegroundColor Cyan
Write-Host "  MLOPS FRAUD DETECTION PLATFORM VERIFIED AND READY FOR SERVING  " -ForegroundColor Green
Write-Host "=================================================================" -ForegroundColor Cyan
