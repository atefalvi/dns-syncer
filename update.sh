#!/usr/bin/env bash
# DNS Syncer updater — downloads the latest GitHub release and reinstalls.
#
# Usage:
#   sudo bash update.sh            # update in place
#   sudo update.sh --detach        # used by the web UI: re-runs itself via
#                                  # systemd-run so it survives the service restart
set -euo pipefail

REPO="atefalvi/dns-syncer"
SELF="/opt/dns-syncer/update.sh"
STATE_DIR="/var/lib/dns-syncer"
LOG_DIR="/var/log/dns-syncer"
STATUS_FILE="$STATE_DIR/update-status.json"
LOG_FILE="$LOG_DIR/update.log"

timestamp() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }

write_status() {
  local status="$1"
  local message="$2"
  local version="${3:-}"
  mkdir -p "$STATE_DIR" "$LOG_DIR"
  printf '{"status":"%s","timestamp":"%s","message":"%s","version":"%s"}\n' \
    "$status" "$(timestamp)" "$message" "$version" > "$STATUS_FILE"
}

[ "$(id -u)" -eq 0 ] || { echo "Run as root: sudo bash update.sh"; exit 1; }

if [ "${1:-}" = "--detach" ]; then
  write_status "queued" "Detached updater queued"
  systemd-run --unit=dns-syncer-update --collect \
    --property=WorkingDirectory=/opt/dns-syncer /bin/bash "$SELF" \
    || { write_status "failed" "Could not start detached updater"; exit 1; }
  exit 0
fi

mkdir -p "$STATE_DIR" "$LOG_DIR"
exec > >(tee -a "$LOG_FILE") 2>&1
write_status "running" "Updater started"

command -v curl >/dev/null || { apt-get update -qq && apt-get install -y -qq curl; }

TMP=$(mktemp -d)
trap 'rc=$?; if [ "$rc" -ne 0 ]; then write_status "failed" "Update failed; see update.log"; fi; rm -rf "$TMP"; exit "$rc"' EXIT

TAG=$(curl -fsSL "https://api.github.com/repos/$REPO/releases/latest" \
        -H "Accept: application/vnd.github+json" \
      | grep -m1 '"tag_name"' | cut -d'"' -f4 || true)

if [ -n "$TAG" ]; then
  URL="https://github.com/$REPO/archive/refs/tags/$TAG.tar.gz"
else
  echo "No release found; using main branch."
  URL="https://github.com/$REPO/archive/refs/heads/main.tar.gz"
fi

echo "Downloading DNS Syncer ${TAG:-main}..."
write_status "running" "Downloading DNS Syncer ${TAG:-main}" "${TAG:-main}"
curl -fsSL "$URL" | tar -xz -C "$TMP" --strip-components=1

bash "$TMP/installer/install.sh"

echo
echo "✓ DNS Syncer updated to ${TAG:-latest main}"
write_status "success" "DNS Syncer updated to ${TAG:-latest main}" "${TAG:-latest main}"
