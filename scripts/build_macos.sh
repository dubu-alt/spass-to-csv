#!/usr/bin/env bash
set -euo pipefail

python3 -m pip install --upgrade pip
python3 -m pip install ".[build]"
python3 -m PyInstaller \
  --name "SPass CSV Converter" \
  --windowed \
  --onefile \
  --clean \
  --paths src \
  --collect-all tkinterdnd2 \
  scripts/pyinstaller_entry.py

echo "macOS app created in dist/"
