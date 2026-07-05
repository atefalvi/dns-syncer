"""App-wide constants and default config."""
from app import VERSION

DEFAULT_IP_URL = "https://api.ipify.org"
IP_TIMEOUT = 8.0
CLOUDFLARE_API = "https://api.cloudflare.com/client/v4"
HTTP_TIMEOUT = 15.0
USER_AGENT = "dns-syncer/0.1 (+https://datadreamer)"

RETRY_ATTEMPTS = 3
RETRY_DELAYS = [2, 5]  # seconds between attempts

MAX_LOG_ENTRIES = 1000

# GitHub repo used for release update checks and the updater script.
GITHUB_REPO = "atefalvi/dns-syncer"
UPDATE_SCRIPT = "/opt/dns-syncer/update.sh"

# Events that integrations may subscribe to.
TRIGGER_EVENTS = [
    "SYNC_COMPLETE",
    "SYNC_FAILED",
    "RECORD_UPDATED",
    "RECORD_UPDATE_FAILED",
    "TOKEN_INVALID",
    "SERVICE_STARTED",
]


def default_config() -> dict:
    return {
        "version": VERSION,
        "sync_interval_minutes": 30,
        "run_on_startup": True,
        "ip_provider": {"name": "ipify", "url": DEFAULT_IP_URL, "type": "ipv4"},
        "cloudflare": {"selected_zone_id": "", "selected_zone_name": ""},
        "records": [],
        "integrations": [],
        "logging": {"retention_days": 30, "max_entries": MAX_LOG_ENTRIES},
        "ui": {"host": "0.0.0.0", "port": 5055},
        "advanced": {
            "user_agent": USER_AGENT,
            "retry_attempts": RETRY_ATTEMPTS,
            "retry_delays": RETRY_DELAYS,
        },
    }
