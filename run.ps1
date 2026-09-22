# Run Sales Analytics Dashboard on localhost and open in Chrome
$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
Set-Location $projectRoot

$port = 8501
$url = "http://localhost:$port"

# Try to find Python (venv, then py, then python)
$pythonCmd = $null
if (Test-Path "venv\Scripts\python.exe") {
    $pythonCmd = "venv\Scripts\python.exe"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py"
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
}

if (-not $pythonCmd) {
    Write-Host "Python not found in PATH." -ForegroundColor Red
    Write-Host "  - Install Python from https://www.python.org/ (add to PATH during install)" -ForegroundColor Yellow
    Write-Host "  - Then run: pip install -r requirements.txt" -ForegroundColor Yellow
    Write-Host "  - Then run this script again, or run: streamlit run app.py --server.port=8501" -ForegroundColor Yellow
    $open = Read-Host "Open Chrome to $url anyway? (y/n)"
    if ($open -eq "y") { Start-Process "chrome" -ArgumentList $url -ErrorAction SilentlyContinue; Start-Process $url }
    exit 1
}

# Open Chrome after a short delay (so server has time to start)
$job = Start-Job -ScriptBlock {
    param($u)
    Start-Sleep -Seconds 4
    try {
        Start-Process "chrome" -ArgumentList $u -ErrorAction SilentlyContinue
    } catch {
        Start-Process $u
    }
} -ArgumentList $url

Write-Host "Starting dashboard at $url ... Chrome will open shortly." -ForegroundColor Green

# Run Streamlit on localhost
if ($pythonCmd -match "venv") {
    & "$projectRoot\$pythonCmd" -m streamlit run app.py --server.address=localhost --server.port=$port
} else {
    & $pythonCmd -m streamlit run app.py --server.address=localhost --server.port=$port
}

Remove-Job $job -Force -ErrorAction SilentlyContinue
