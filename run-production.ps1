$ErrorActionPreference = 'Stop'

$env:RECEIPT_SECRET_KEY = if ($env:RECEIPT_SECRET_KEY) { $env:RECEIPT_SECRET_KEY } else { 'change-this-before-internet-exposure' }
$env:RECEIPT_PORT = if ($env:RECEIPT_PORT) { $env:RECEIPT_PORT } else { '5000' }

Write-Host "Installing dependencies..."
.\venv\Scripts\python.exe -m pip install -r .\requirements.txt

Write-Host "Starting production server on port $env:RECEIPT_PORT ..."
.\venv\Scripts\python.exe .\wsgi.py
