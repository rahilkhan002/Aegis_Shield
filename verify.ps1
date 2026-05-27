# verify.ps1
# Automates the setup, model training, and testing of the MLOps Fraud Pipeline.

$ErrorActionPreference = "Stop"

Write-Host "=== Phase 1: Creating Virtual Environment ===" -ForegroundColor Cyan
if (-not (Test-Path ".venv")) {
    py -3.11 -m venv .venv
    Write-Host "Virtual environment created successfully using Python 3.11." -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists. Skipping creation." -ForegroundColor Yellow
}

Write-Host "`n=== Phase 2: Activating Environment & Installing Requirements ===" -ForegroundColor Cyan
# Activate virtual environment
. .venv\Scripts\Activate.ps1

Write-Host "Upgrading pip..." -ForegroundColor Gray
python -m pip install --upgrade pip

Write-Host "Installing dependencies from requirements.txt..." -ForegroundColor Gray
pip install -r requirements.txt
Write-Host "Dependencies installed successfully." -ForegroundColor Green

Write-Host "`n=== Phase 3: Training the Model ===" -ForegroundColor Cyan
python -m app.model
if ((Test-Path "model.pkl") -and (Test-Path "scaler.pkl")) {
    Write-Host "Model and Scaler serialized artifacts found in project root." -ForegroundColor Green
} else {
    Write-Error "Failed to locate trained model artifacts."
}

Write-Host "`n=== Phase 4: Running Unit Tests ===" -ForegroundColor Cyan
pytest tests/ -v
Write-Host "All tests completed successfully." -ForegroundColor Green
