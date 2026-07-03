#!/usr/bin/env bash
# Run DNS Syncer locally against ./.local (no root, no systemd).
set -euo pipefail
cd "$(dirname "$0")/../backend"
[ -d .venv ] || python3 -m venv .venv
.venv/bin/pip install -q -e ".[dev]"
DNS_SYNCER_DEV=1 exec .venv/bin/uvicorn app.main:app --reload --port 5055
