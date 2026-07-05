"""Local HTTP API. All routes are mounted under /api by main.py."""
import os
import subprocess
import time
import uuid

import httpx
from fastapi import APIRouter, HTTPException, Query, Response

from app import VERSION
from app.settings import GITHUB_REPO, UPDATE_SCRIPT
from app import (cloudflare_client as cf, config_store, integration_engine,
                 ip_provider, log_store, secret_store, sync_engine)
from app.models import (AppSettings, IntegrationConfig, IntegrationPatch,
                        RecordCreate, RecordPatch, TokenBody)

router = APIRouter(prefix="/api")
_START = time.time()


def _systemd_active(unit: str) -> str:
    try:
        out = subprocess.run(["systemctl", "is-active", unit],
                             capture_output=True, text=True, timeout=3)
        return out.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


# --- health / status ---

@router.get("/health")
def health():
    return {"status": "ok", "version": VERSION,
            "uptime_seconds": int(time.time() - _START)}


@router.get("/status")
def status():
    cfg = config_store.load()
    state = sync_engine.read_state()
    records = cfg.get("records", [])
    ok = sum(1 for r in records if r.get("status") in ("synced", "updated"))
    token_status = "valid" if secret_store.get_token() else "missing"
    app_status = "healthy"
    if state.get("last_error"):
        app_status = "degraded"
    if token_status == "missing":
        app_status = "setup"
    return {
        "app_status": app_status,
        "current_ip": state.get("last_public_ip"),
        "last_sync_at": state.get("last_sync_at"),
        "next_sync_hint": f"{cfg.get('sync_interval_minutes', 30)} minutes",
        "records_total": len(records),
        "records_ok": ok,
        "token_status": token_status,
        "token_masked": secret_store.token_masked(),
        "service_status": _systemd_active("dns-syncer.service"),
        "timer_status": _systemd_active("dns-syncer.timer"),
    }


# --- updates ---

def _ver_tuple(v: str) -> tuple:
    try:
        return tuple(int(x) for x in v.strip().lstrip("v").split("."))
    except ValueError:
        return ()


@router.get("/update/check")
def update_check():
    try:
        r = httpx.get(f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest",
                      timeout=10, headers={"User-Agent": "dns-syncer",
                                           "Accept": "application/vnd.github+json"})
        r.raise_for_status()
        latest = r.json().get("tag_name", "").lstrip("v")
    except Exception as e:
        raise HTTPException(502, f"Update check failed: {e}")
    return {
        "current": VERSION,
        "latest": latest,
        "update_available": bool(latest) and _ver_tuple(latest) > _ver_tuple(VERSION),
    }


@router.post("/update/run")
def update_run():
    if not os.path.exists(UPDATE_SCRIPT):
        raise HTTPException(400, "Updater not installed. Run on the device: "
                                 "sudo bash update.sh (from the dns-syncer repo)")
    # systemd-run detaches the update from this service's cgroup, so the
    # updater survives the service restart it performs.
    proc = subprocess.run(["sudo", "-n", UPDATE_SCRIPT, "--detach"],
                          capture_output=True, text=True, timeout=30)
    if proc.returncode != 0:
        raise HTTPException(502, "Could not start updater: "
                            + (proc.stderr.strip() or "sudo not permitted. "
                               "Re-run the installer, or run: sudo /opt/dns-syncer/update.sh"))
    log_store.append("INFO", "UPDATE_STARTED", "Update started from web UI")
    return {"started": True, "message": "Updating — the app restarts in about a minute."}


# --- sync ---

@router.post("/sync/run")
def sync_run():
    return sync_engine.run_sync()


# --- records ---

@router.get("/records")
def records_list():
    return config_store.load().get("records", [])


@router.post("/records")
def records_create(body: RecordCreate):
    cfg = config_store.load()
    zone_id = body.zone_id or cfg["cloudflare"]["selected_zone_id"]
    zone_name = body.zone_name or cfg["cloudflare"]["selected_zone_name"]
    if not zone_id or not zone_name:
        raise HTTPException(400, "No zone selected")
    if not secret_store.get_token():
        raise HTTPException(400, "Cloudflare token not set")

    host = body.hostname.strip()
    fqdn = zone_name if host in ("", "@", zone_name) else f"{host}.{zone_name}"

    try:
        found = cf.find_record(zone_id, fqdn, body.type)
        if found:
            record_id, current = found["id"], found["content"]
            proxied = found.get("proxied", body.proxied)
        else:
            ip = ip_provider.get_public_ip()
            created = cf.create_record(zone_id, fqdn, body.type, ip, body.proxied)
            record_id, current, proxied = created["id"], created["content"], created.get("proxied", body.proxied)
    except cf.CloudflareError as e:
        raise HTTPException(502, e.message)
    except Exception as e:
        raise HTTPException(502, f"Public IP lookup failed: {e}")

    rec = {
        "id": f"rec_{uuid.uuid4().hex[:8]}", "enabled": body.enabled,
        "zone_id": zone_id, "zone_name": zone_name, "record_id": record_id,
        "hostname": host, "fqdn": fqdn, "type": body.type, "proxied": proxied,
        "target_ip": "", "cloudflare_value": current, "status": "unknown",
        "last_checked_at": None, "last_updated_at": None,
    }
    cfg.setdefault("records", []).append(rec)
    config_store.save(cfg)
    log_store.append("INFO", "RECORD_ADDED", f"Added {fqdn}", record=fqdn)
    return rec


@router.patch("/records/{rec_id}")
def records_patch(rec_id: str, body: RecordPatch):
    cfg = config_store.load()
    for rec in cfg.get("records", []):
        if rec["id"] == rec_id:
            if body.enabled is not None:
                rec["enabled"] = body.enabled
            if body.proxied is not None:
                rec["proxied"] = body.proxied
                # push proxied change to Cloudflare with existing content
                try:
                    cf.update_record(rec["zone_id"], rec["record_id"], rec["fqdn"],
                                     rec["type"], rec["cloudflare_value"] or "0.0.0.0",
                                     body.proxied)
                except cf.CloudflareError:
                    pass
            config_store.save(cfg)
            return rec
    raise HTTPException(404, "Record not found")


@router.delete("/records/{rec_id}")
def records_delete(rec_id: str):
    cfg = config_store.load()
    before = len(cfg.get("records", []))
    cfg["records"] = [r for r in cfg.get("records", []) if r["id"] != rec_id]
    if len(cfg["records"]) == before:
        raise HTTPException(404, "Record not found")
    config_store.save(cfg)
    return {"deleted": rec_id}


# --- logs ---

@router.get("/logs")
def logs(level: str = None, event: str = None, filter: str = "all",
         q: str = None, page: int = 1, page_size: int = 50):
    result = log_store.query(level=level, event=event, filter_tab=filter,
                             q=q, page=page, page_size=page_size)
    result["counts"] = log_store.counts()
    return result


@router.get("/logs/export")
def logs_export():
    return Response(log_store.as_csv(), media_type="text/csv",
                    headers={"Content-Disposition": "attachment; filename=dns-syncer-logs.csv"})


@router.delete("/logs")
def logs_clear():
    log_store.clear()
    return {"cleared": True}


# --- settings ---

@router.get("/settings")
def settings_get():
    cfg = config_store.load()
    return {
        "sync_interval_minutes": cfg["sync_interval_minutes"],
        "ip_provider": cfg["ip_provider"]["name"],
        "ip_provider_url": cfg["ip_provider"]["url"],
        "log_retention_days": cfg["logging"]["retention_days"],
        "max_log_entries": cfg["logging"]["max_entries"],
        "run_on_startup": cfg["run_on_startup"],
        "cloudflare_zone_id": cfg["cloudflare"]["selected_zone_id"],
        "cloudflare_zone_name": cfg["cloudflare"]["selected_zone_name"],
        "ui_bind_host": cfg["ui"]["host"],
        "ui_port": cfg["ui"]["port"],
        "advanced": cfg.get("advanced", {}),
    }


@router.patch("/settings")
def settings_patch(body: AppSettings):
    cfg = config_store.load()
    m = {
        "sync_interval_minutes": ("sync_interval_minutes",),
        "run_on_startup": ("run_on_startup",),
        "ip_provider": ("ip_provider", "name"),
        "ip_provider_url": ("ip_provider", "url"),
        "log_retention_days": ("logging", "retention_days"),
        "max_log_entries": ("logging", "max_entries"),
        "cloudflare_zone_id": ("cloudflare", "selected_zone_id"),
        "cloudflare_zone_name": ("cloudflare", "selected_zone_name"),
        "ui_bind_host": ("ui", "host"),
        "ui_port": ("ui", "port"),
    }
    for field, path in m.items():
        val = getattr(body, field)
        if val is None:
            continue
        target = cfg
        for key in path[:-1]:
            target = target[key]
        target[path[-1]] = val
    config_store.save(cfg)
    log_store.append("INFO", "SETTINGS_UPDATED", "Settings updated")
    return settings_get()


# --- cloudflare token / zones / records ---

@router.post("/cloudflare/token")
def token_set(body: TokenBody):
    secret_store.set_token(body.token.strip())
    return {"token_masked": secret_store.token_masked()}


@router.post("/cloudflare/token/verify")
def token_verify():
    result = cf.verify_token()
    if result["valid"]:
        log_store.append("INFO", "TOKEN_VERIFIED", "Cloudflare token verified")
    else:
        log_store.append("WARN", "TOKEN_INVALID", f"Token invalid: {result['message']}")
        integration_engine.dispatch("TOKEN_INVALID",
                                    {"message": "Cloudflare token invalid",
                                     "status": "invalid", "error": result["message"],
                                     "timestamp": log_store._now()})
    return result


@router.get("/cloudflare/zones")
def zones():
    try:
        return {"zones": cf.list_zones()}
    except cf.CloudflareError as e:
        raise HTTPException(502, e.message)


@router.get("/cloudflare/records")
def cf_records(zone_id: str = Query(...)):
    try:
        return {"records": cf.list_records(zone_id)}
    except cf.CloudflareError as e:
        raise HTTPException(502, e.message)


# --- integrations ---

def _public_integration(integ: dict) -> dict:
    """Return integration without secret URL; flag whether one is stored."""
    out = {k: v for k, v in integ.items()}
    out["connected"] = bool(secret_store.get_integration_url(integ["id"]))
    out.pop("url", None)
    return out


@router.get("/integrations")
def integrations_list():
    return [_public_integration(i) for i in config_store.load().get("integrations", [])]


@router.post("/integrations")
def integrations_create(body: IntegrationConfig):
    cfg = config_store.load()
    int_id = f"int_{uuid.uuid4().hex[:8]}"
    integ = {
        "id": int_id, "enabled": body.enabled, "name": body.name, "type": body.type,
        "trigger_events": body.trigger_events, "method": body.method,
        "headers": {}, "body_template": body.body_template,
    }
    cfg.setdefault("integrations", []).append(integ)
    config_store.save(cfg)
    secret_store.set_integration_secrets(int_id, body.url, body.headers)
    return _public_integration(integ)


@router.patch("/integrations/{int_id}")
def integrations_patch(int_id: str, body: IntegrationPatch):
    cfg = config_store.load()
    for integ in cfg.get("integrations", []):
        if integ["id"] == int_id:
            for field in ("enabled", "name", "trigger_events", "method", "body_template"):
                val = getattr(body, field)
                if val is not None:
                    integ[field] = val
            config_store.save(cfg)
            if body.url or body.headers is not None:
                secret_store.set_integration_secrets(int_id, body.url or "", body.headers)
            return _public_integration(integ)
    raise HTTPException(404, "Integration not found")


@router.delete("/integrations/{int_id}")
def integrations_delete(int_id: str):
    cfg = config_store.load()
    before = len(cfg.get("integrations", []))
    cfg["integrations"] = [i for i in cfg.get("integrations", []) if i["id"] != int_id]
    if len(cfg["integrations"]) == before:
        raise HTTPException(404, "Integration not found")
    config_store.save(cfg)
    secret_store.delete_integration(int_id)
    return {"deleted": int_id}


@router.post("/integrations/{int_id}/test")
def integrations_test(int_id: str):
    for integ in config_store.load().get("integrations", []):
        if integ["id"] == int_id:
            return integration_engine.send_test(integ)
    raise HTTPException(404, "Integration not found")
