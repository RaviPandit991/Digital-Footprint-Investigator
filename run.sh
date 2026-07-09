#!/usr/bin/env bash
# Convenience launcher for Digital Footprint Investigator
set -e
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate

pip install -q --upgrade pip
pip install -q -r backend/requirements.txt

echo ""
echo "Launching Digital Footprint Investigator..."
python -m backend.app
