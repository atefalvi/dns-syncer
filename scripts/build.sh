#!/usr/bin/env bash
# No frontend build step — the UI is static HTML/CSS/vanilla JS served as-is.
# This script only builds the Python wheel, for packaging.
set -euo pipefail
cd "$(dirname "$0")/../backend"
python3 -m pip install -q build
python3 -m build
echo "Frontend needs no build; static files ship under frontend/."
