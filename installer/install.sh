#!/usr/bin/env bash
# DNS Syncer installer. Run as root on a Debian-based systemd host.
set -euo pipefail

APP=dns-syncer
APP_DIR=/opt/$APP
CFG_DIR=/etc/$APP
STATE_DIR=/var/lib/$APP
LOG_DIR=/var/log/$APP
USER=$APP
PORT=5055
SRC="$(cd "$(dirname "$0")/.." && pwd)"

echo "DNS Syncer installer"
echo

[ "$(uname -s)" = "Linux" ] || { echo "✗ Linux required"; exit 1; }
command -v systemctl >/dev/null || { echo "✗ systemd required"; exit 1; }
echo "✓ systemd detected"

if command -v python3 >/dev/null; then
  PY=$(python3 -c 'import sys; print("%d.%d"%sys.version_info[:2])')
  echo "✓ Python $PY detected"
else
  echo "Installing python3..."; apt-get update -qq && apt-get install -y -qq python3 python3-venv
fi
python3 -m venv --help >/dev/null 2>&1 || apt-get install -y -qq python3-venv

id -u "$USER" >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$USER"
echo "✓ Created service user"

install -d -o "$USER" -g "$USER" -m 0755 "$APP_DIR"
install -d -o "$USER" -g "$USER" -m 0750 "$CFG_DIR" "$STATE_DIR" "$LOG_DIR"

cp -r "$SRC/backend/app" "$APP_DIR/"
cp "$SRC/backend/pyproject.toml" "$APP_DIR/"
cp -r "$SRC/frontend" "$APP_DIR/"
chown -R "$USER:$USER" "$APP_DIR"
echo "✓ Installed backend"
echo "✓ Installed frontend"

python3 -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/pip" install -q --upgrade pip
"$APP_DIR/.venv/bin/pip" install -q "$APP_DIR"
chown -R "$USER:$USER" "$APP_DIR/.venv"

cp "$SRC/systemd/"*.service "$SRC/systemd/"*.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now $APP.service >/dev/null
systemctl enable --now $APP.timer >/dev/null
echo "✓ Started service"
echo "✓ Started timer"

IP=$(hostname -I 2>/dev/null | awk '{print $1}')
echo
echo "DNS Syncer installed."
echo
echo "Open http://${IP:-<device-ip>}:$PORT"
echo "Configuration happens in the web app."
