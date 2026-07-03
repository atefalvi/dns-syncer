#!/usr/bin/env bash
# DNS Syncer uninstaller. Run as root.
set -euo pipefail

APP=dns-syncer
echo "DNS Syncer uninstaller"

systemctl disable --now $APP.timer 2>/dev/null || true
systemctl disable --now $APP.service 2>/dev/null || true
rm -f /etc/systemd/system/$APP.service /etc/systemd/system/$APP-sync.service /etc/systemd/system/$APP.timer
systemctl daemon-reload
echo "✓ Services stopped and removed"

rm -rf /opt/$APP
echo "✓ Removed /opt/$APP"

read -rp "Remove configuration and logs? [y/N] " ans
if [ "${ans:-N}" = "y" ] || [ "${ans:-N}" = "Y" ]; then
  rm -rf /etc/$APP /var/lib/$APP /var/log/$APP
  userdel $APP 2>/dev/null || true
  echo "✓ Removed config, state, logs, and user"
else
  echo "Kept /etc/$APP, /var/lib/$APP, /var/log/$APP"
fi
echo "Done."
