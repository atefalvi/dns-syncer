#!/usr/bin/env bash
# Lightweight checks: Python syntax compile + pytest. No extra tooling required.
set -euo pipefail
cd "$(dirname "$0")/../backend"
.venv/bin/python -m compileall -q app
.venv/bin/python -m pytest -q
