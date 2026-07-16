"""Outbound webhooks. Discord/Slack/Teams are just generic HTTP POSTs.

URLs and custom headers live in the encrypted secret store, keyed by integration
id, and are never logged.
"""
import json
import re

import httpx

from app import config_store, log_store, secret_store
from app.settings import HTTP_TIMEOUT, USER_AGENT

_TOKEN_RE = re.compile(r"{{\s*([A-Za-z0-9_]+)\s*}}")


def _stringify(val) -> str:
    if val is None:
        return ""
    if isinstance(val, (dict, list)):
        return json.dumps(val, separators=(",", ":"))
    return str(val)


def render(template, ctx: dict):
    """Recursively substitute {{var}} tokens in strings within a template.

    Unknown variables render as empty strings so webhook receivers never see raw
    template tokens such as ``{{record_name}}``.
    """
    if isinstance(template, str):
        exact = _TOKEN_RE.fullmatch(template.strip())
        if exact:
            return ctx.get(exact.group(1), "")
        return _TOKEN_RE.sub(lambda m: _stringify(ctx.get(m.group(1), "")), template)
    if isinstance(template, dict):
        return {k: render(v, ctx) for k, v in template.items()}
    if isinstance(template, list):
        return [render(v, ctx) for v in template]
    return template


def _send(integ: dict, ctx: dict) -> dict:
    int_id = integ["id"]
    url = secret_store.get_integration_url(int_id)
    if not url:
        raise ValueError("No URL configured")
    headers = {"User-Agent": USER_AGENT, "Content-Type": "application/json"}
    headers.update(integ.get("headers", {}))
    headers.update(secret_store.get_integration_headers(int_id))
    body = render(integ.get("body_template") or {"content": "{{message}}"}, ctx)
    method = (integ.get("method") or "POST").upper()

    resp = httpx.request(method, url, headers=headers,
                         content=json.dumps(body), timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    return {"status": resp.status_code}


def send_test(integ: dict) -> dict:
    ctx = {"event": "TEST", "status": "test", "message": "DNS Syncer test payload",
           "old_ip": "203.0.113.1", "new_ip": "203.0.113.42",
           "record_name": "home.example.com", "record_type": "A",
           "zone": "example.com", "timestamp": log_store._now(),
           "duration_ms": 0, "error": ""}
    try:
        res = _send(integ, ctx)
        log_store.append("INFO", "INTEGRATION_SENT", f"Test sent to {integ['name']}")
        return {"ok": True, **res}
    except Exception as e:
        log_store.append("ERROR", "INTEGRATION_FAILED", f"Test to {integ['name']} failed: {e}")
        return {"ok": False, "error": str(e)}


def dispatch(event: str, ctx: dict) -> None:
    """Fire every enabled integration subscribed to `event`."""
    ctx = {"event": event, **ctx}
    for integ in config_store.load().get("integrations", []):
        if not integ.get("enabled", True):
            continue
        if event not in integ.get("trigger_events", []):
            continue
        try:
            _send(integ, ctx)
            log_store.append("INFO", "INTEGRATION_SENT",
                             f"Sent {event} to {integ['name']}")
        except Exception as e:
            log_store.append("ERROR", "INTEGRATION_FAILED",
                             f"{integ['name']} failed: {e}", details={"event": event})
