"""The sync cycle: detect IP, compare each record against Cloudflare, update on
change with bounded retries, log every step, fire integrations."""
import json
import time
from datetime import datetime, timezone

from app import cloudflare_client as cf
from app import config_store, integration_engine, ip_provider, log_store, paths
from app.cloudflare_client import CloudflareError


# --- state.json helpers (small enough to live here) ---

def read_state() -> dict:
    if paths.STATE_FILE.exists():
        try:
            return json.loads(paths.STATE_FILE.read_text())
        except json.JSONDecodeError:
            pass
    return {"last_public_ip": None, "last_sync_at": None,
            "last_successful_sync_at": None, "last_error": None}


def write_state(state: dict) -> None:
    paths.ensure_dirs()
    paths.STATE_FILE.write_text(json.dumps(state, indent=2))


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _retry_config():
    adv = config_store.load().get("advanced", {})
    return adv.get("retry_attempts", 3), adv.get("retry_delays", [2, 5])


def _update_with_retry(rec: dict, public_ip: str) -> dict:
    """Update one record, retrying only transient failures. Returns the record dict."""
    attempts, delays = _retry_config()
    last_err = None
    for attempt in range(attempts):
        try:
            cf.update_record(rec["zone_id"], rec["record_id"], rec["fqdn"],
                             rec["type"], public_ip, rec.get("proxied", True))
            return {"status": "updated"}
        except CloudflareError as e:
            last_err = e
            if not e.retryable or attempt == attempts - 1:
                break
            time.sleep(delays[min(attempt, len(delays) - 1)])
    return {"status": "failed", "error": last_err.message if last_err else "unknown"}


def run_sync() -> dict:
    started = _now()
    t0 = time.time()
    log_store.append("INFO", "SYNC_START", "Starting sync cycle")

    cfg = config_store.load()
    records = [r for r in cfg.get("records", []) if r.get("enabled", True)]
    state = read_state()

    # 1. public IP
    try:
        public_ip = ip_provider.get_public_ip()
        log_store.append("INFO", "IP_DETECTED", "Public IP detected",
                         details={"ip": public_ip})
    except Exception as e:
        msg = f"Could not detect public IP: {e}"
        log_store.append("ERROR", "SYNC_FAILED", msg)
        state.update({"last_sync_at": started, "last_error": msg})
        write_state(state)
        integration_engine.dispatch("SYNC_FAILED", {"message": msg, "status": "failed",
                                                    "error": str(e), "timestamp": started})
        return {"status": "error", "started_at": started, "completed_at": _now(),
                "public_ip": None, "records_checked": 0, "records_updated": 0,
                "records_failed": 0, "message": msg}

    if state.get("last_public_ip") == public_ip:
        log_store.append("INFO", "IP_UNCHANGED", "Public IP unchanged",
                         details={"ip": public_ip})

    checked = updated = failed = 0
    for rec in cfg.get("records", []):
        if not rec.get("enabled", True):
            rec["status"] = "paused"
            continue
        checked += 1
        rec["target_ip"] = public_ip
        rec["last_checked_at"] = _now()

        current = rec.get("cloudflare_value")
        log_store.append("INFO", "RECORD_CHECKED", f"Checked {rec['fqdn']}",
                         record=rec["fqdn"], details={"current": current, "target": public_ip})

        if current == public_ip:
            rec["status"] = "synced"
            log_store.append("INFO", "RECORD_UNCHANGED", f"{rec['fqdn']} already current",
                             record=rec["fqdn"])
            continue

        result = _update_with_retry(rec, public_ip)
        if result["status"] == "updated":
            old = current
            rec["cloudflare_value"] = public_ip
            rec["status"] = "updated"
            rec["last_updated_at"] = _now()
            updated += 1
            log_store.append("INFO", "RECORD_UPDATED", f"{rec['type']} record updated",
                             record=rec["fqdn"], details={"old_ip": old, "new_ip": public_ip})
            integration_engine.dispatch("RECORD_UPDATED", {
                "message": f"{rec['fqdn']} updated to {public_ip}", "status": "updated",
                "old_ip": old, "new_ip": public_ip, "record_name": rec["fqdn"],
                "record_type": rec["type"], "zone": rec.get("zone_name", ""),
                "timestamp": rec["last_updated_at"]})
        else:
            rec["status"] = "failed"
            failed += 1
            log_store.append("ERROR", "RECORD_UPDATE_FAILED", f"{rec['fqdn']} update failed",
                             record=rec["fqdn"], details={"error": result.get("error")})
            integration_engine.dispatch("RECORD_UPDATE_FAILED", {
                "message": f"{rec['fqdn']} update failed", "status": "failed",
                "record_name": rec["fqdn"], "record_type": rec["type"],
                "zone": rec.get("zone_name", ""), "error": result.get("error", ""),
                "timestamp": _now()})

    config_store.save(cfg)

    completed = _now()
    duration_ms = int((time.time() - t0) * 1000)
    status = "success" if failed == 0 else "partial"
    state.update({"last_public_ip": public_ip, "last_sync_at": completed,
                  "last_error": None if failed == 0 else f"{failed} record(s) failed"})
    if failed == 0:
        state["last_successful_sync_at"] = completed
    write_state(state)

    msg = f"{updated} updated, {checked - updated - failed} unchanged, {failed} failed"
    log_store.append("INFO" if failed == 0 else "WARN", "SYNC_COMPLETE",
                     msg, details={"duration_ms": duration_ms})
    integration_engine.dispatch("SYNC_COMPLETE", {
        "message": msg, "status": status, "new_ip": public_ip,
        "timestamp": completed, "duration_ms": duration_ms})

    return {"status": status, "started_at": started, "completed_at": completed,
            "public_ip": public_ip, "records_checked": checked,
            "records_updated": updated, "records_failed": failed}
