"""CLI entry point for the systemd oneshot and manual ops."""
import json
import sys

from app import cloudflare_client as cf
from app import config_store, log_store, sync_engine


def sync_once() -> int:
    result = sync_engine.run_sync()
    print(json.dumps(result, indent=2))
    return 0 if result["status"] in ("success", "partial") else 1


def verify_token() -> int:
    result = cf.verify_token()
    print(json.dumps(result, indent=2))
    return 0 if result["valid"] else 1


def print_status() -> int:
    cfg = config_store.load()
    state = sync_engine.read_state()
    print(json.dumps({
        "records": len(cfg.get("records", [])),
        "last_sync_at": state.get("last_sync_at"),
        "last_public_ip": state.get("last_public_ip"),
        "last_error": state.get("last_error"),
    }, indent=2))
    return 0


def main(argv=None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    cmd = argv[0] if argv else ""
    if cmd == "sync-once":
        return sync_once()
    if cmd == "verify-token":
        return verify_token()
    if cmd == "print-status":
        return print_status()
    print("usage: python -m app.cli {sync-once|verify-token|print-status}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
