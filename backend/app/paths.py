"""Filesystem paths. Production uses /etc, /var; dev falls back to ./.local.

Mode is production when /etc/dns-syncer exists and is writable, unless
DNS_SYNCER_DEV forces dev mode. Override the whole tree with DNS_SYNCER_HOME.
"""
import os
from pathlib import Path

_PROD_CONFIG = Path("/etc/dns-syncer")
_PROD_STATE = Path("/var/lib/dns-syncer")
_PROD_LOG = Path("/var/log/dns-syncer")


def _is_prod() -> bool:
    if os.environ.get("DNS_SYNCER_DEV"):
        return False
    return _PROD_CONFIG.is_dir() and os.access(_PROD_CONFIG, os.W_OK)


if os.environ.get("DNS_SYNCER_HOME"):
    _home = Path(os.environ["DNS_SYNCER_HOME"])
    CONFIG_DIR = STATE_DIR = LOG_DIR = _home
elif _is_prod():
    CONFIG_DIR, STATE_DIR, LOG_DIR = _PROD_CONFIG, _PROD_STATE, _PROD_LOG
else:
    _local = Path.cwd() / ".local"
    CONFIG_DIR = STATE_DIR = LOG_DIR = _local

CONFIG_FILE = CONFIG_DIR / "config.json"
SECRETS_KEY_FILE = CONFIG_DIR / "secrets.key"
SECRETS_ENC_FILE = CONFIG_DIR / "secrets.enc"
STATE_FILE = STATE_DIR / "state.json"
LOG_FILE = LOG_DIR / "events.jsonl"

# Static frontend, resolved relative to the installed app layout.
FRONTEND_DIR = Path(os.environ.get("DNS_SYNCER_FRONTEND", Path(__file__).resolve().parents[2] / "frontend"))


def ensure_dirs() -> None:
    for d in {CONFIG_DIR, STATE_DIR, LOG_DIR}:
        d.mkdir(parents=True, exist_ok=True)
