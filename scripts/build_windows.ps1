$ErrorActionPreference = "Stop"

py -m pip install --upgrade pip
py -m pip install ".[build]"
py -m PyInstaller `
  --name "SPass CSV Converter" `
  --windowed `
  --onefile `
  --clean `
  --paths src `
  --collect-all tkinterdnd2 `
  src/spass_csv_converter/__main__.py

Write-Host "Windows app created in dist/"
