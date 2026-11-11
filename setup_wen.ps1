$targetPython = "C:\Users\zamst\AppData\Local\Programs\Python\Python312\python.exe"

if (-not (Test-Path $targetPython)) {
    Write-Error "Python 3.12 not found at $targetPython"
    exit 1
}

$env:WEN_HOME = "$PSScriptRoot"
Set-Location $env:WEN_HOME

if (-not (Test-Path ".venv")) {
    & $targetPython -m venv .venv
    .\.venv\Scripts\Activate.ps1
    pip install --upgrade pip
    pip install pyside6
} else {
    .\.venv\Scripts\Activate.ps1
}

python main.py
