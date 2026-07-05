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

[ "$(id -u)" -eq 0 ] || { echo "Run as root: sudo bash update.sh"; exit 1; }

if [ "${1:-}" = "--detach" ]; then
  exec systemd-run --unit=dns-syncer-update --collect bash "$SELF"
fi

command -v curl >/dev/null || { apt-get update -qq && apt-get install -y -qq curl; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

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
curl -fsSL "$URL" | tar -xz -C "$TMP" --strip-components=1

bash "$TMP/installer/install.sh"

echo
echo "✓ DNS Syncer updated to ${TAG:-latest main}"
