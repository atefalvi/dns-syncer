"""JSONL event log: append-only with a capped tail, plus filtered reads."""
import json
import time
from datetime import datetime, timezone

from app import paths

# Which events map to each Logs-screen filter tab.
_FILTER_EVENTS = {
    "sync": {"SYNC_START", "SYNC_COMPLETE", "SYNC_FAILED", "IP_DETECTED",
             "IP_UNCHANGED", "RECORD_CHECKED", "RECORD_UPDATED",
             "RECORD_UNCHANGED", "RECORD_UPDATE_FAILED"},
    "token": {"TOKEN_VERIFIED", "TOKEN_INVALID"},
    "integration": {"INTEGRATION_SENT", "INTEGRATION_FAILED"},
}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def append(level: str, event: str, message: str, record: str | None = None,
           details: dict | None = None) -> dict:
    entry = {
        "id": f"log_{int(time.time() * 1000)}",
        "timestamp": _now(),
        "level": level,
        "event": event,
        "record": record,
        "message": message,
        "details": details or {},
    }
    paths.ensure_dirs()
    with open(paths.LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    _trim()
    return entry


def _max_entries() -> int:
    from app import config_store
    return config_store.load().get("logging", {}).get("max_entries", 1000)


def _read_all() -> list[dict]:
    if not paths.LOG_FILE.exists():
        return []
    out = []
    for line in paths.LOG_FILE.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def _trim() -> None:
    cap = _max_entries()
    entries = _read_all()
    if len(entries) <= cap:
        return
    kept = entries[-cap:]
    paths.LOG_FILE.write_text("".join(json.dumps(e) + "\n" for e in kept))


def query(level=None, event=None, filter_tab=None, q=None, page=1, page_size=50) -> dict:
    entries = list(reversed(_read_all()))  # newest first

    if filter_tab and filter_tab != "all":
        if filter_tab == "warnings":
            entries = [e for e in entries if e.get("level") == "WARN"]
        elif filter_tab == "errors":
            entries = [e for e in entries if e.get("level") == "ERROR"]
        elif filter_tab in _FILTER_EVENTS:
            allowed = _FILTER_EVENTS[filter_tab]
            entries = [e for e in entries if e.get("event") in allowed]
    if level:
        entries = [e for e in entries if e.get("level") == level]
    if event:
        entries = [e for e in entries if e.get("event") == event]
    if q:
        needle = q.lower()
        entries = [e for e in entries if needle in json.dumps(e).lower()]

    total = len(entries)
    start = (page - 1) * page_size
    return {
        "page": page,
        "page_size": page_size,
        "total": total,
        "entries": entries[start:start + page_size],
    }


def counts() -> dict:
    entries = _read_all()
    c = {"total": len(entries), "INFO": 0, "DEBUG": 0, "WARN": 0, "ERROR": 0}
    for e in entries:
        lvl = e.get("level")
        if lvl in c:
            c[lvl] += 1
    return c


def recent(n: int = 5) -> list[dict]:
    return list(reversed(_read_all()))[:n]


def clear() -> None:
    if paths.LOG_FILE.exists():
        paths.LOG_FILE.write_text("")


def as_csv() -> str:
    import csv
    import io
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["timestamp", "level", "event", "record", "message", "details"])
    for e in _read_all():
        w.writerow([e.get("timestamp"), e.get("level"), e.get("event"),
                    e.get("record") or "", e.get("message"),
                    json.dumps(e.get("details", {}))])
    return buf.getvalue()
