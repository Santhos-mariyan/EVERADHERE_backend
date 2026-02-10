# start_server.ps1 (fixed)
# Activates venv (if present), installs requirements if venv missing,
# then starts uvicorn.

$venvActivate = Join-Path $PSScriptRoot '.venv\Scripts\Activate.ps1'

if (Test-Path $venvActivate) {
    Write-Host "Activating virtual environment..."
    . "$venvActivate"
} else {
    Write-Host "Virtual environment not found. Creating .venv and installing requirements..."
    python -m venv .venv
    $newActivate = Join-Path $PSScriptRoot '.venv\Scripts\Activate.ps1'
    . "$newActivate"
    python -m pip install --upgrade pip
    if (Test-Path (Join-Path $PSScriptRoot 'requirements.txt')) {
        pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
    }
}

if (-not (Test-Path (Join-Path $PSScriptRoot 'physioclinic.db'))) {
    Write-Host "Warning: physioclinic.db not found in project root. If you need a DB, create or restore it."
}

Write-Host "Starting Uvicorn..."
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
