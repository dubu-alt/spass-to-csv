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
  scripts/pyinstaller_entry.py

Write-Host "Windows app created in dist/"
