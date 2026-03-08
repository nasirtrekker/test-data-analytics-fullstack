#!/usr/bin/env bash
set -euo pipefail

# Creates a single virtual environment and installs the pinned requirements
# Usage: ./setup_venv.sh

HERE=$(cd "$(dirname "$0")" && pwd)
cd "$HERE"

if [ -d .venv ]; then
  echo ".venv already exists — reusing"
else
  python3 -m venv .venv
fi

# activate and install
. .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "\nSetup complete. Activate the venv with:\n  . .venv/bin/activate\n"
