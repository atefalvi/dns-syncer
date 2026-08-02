import pytest

from app import config_store, integration_engine, ip_provider, sync_engine
from app.cloudflare_client import CloudflareError


def _add_record(cloudflare_value):
    cfg = config_store.load()
    cfg["records"] = [{
        "id": "rec_1", "enabled": True, "zone_id": "z1", "zone_name": "example.com",
        "record_id": "r1", "hostname": "home", "fqdn": "home.example.com", "type": "A",
        "proxied": True, "target_ip": "", "cloudflare_value": cloudflare_value,
        "status": "unknown", "last_checked_at": None, "last_updated_at": None,
    }]
    config_store.save(cfg)


@pytest.fixture(autouse=True)
def _no_integrations(monkeypatch):
    monkeypatch.setattr(integration_engine, "dispatch", lambda *a, **k: None)
    monkeypatch.setattr(ip_provider, "get_public_ip", lambda: "203.0.113.42")


def test_no_change(monkeypatch):
    _add_record("203.0.113.42")
    called = []
    monkeypatch.setattr(sync_engine.cf, "update_record", lambda *a, **k: called.append(1))
    res = sync_engine.run_sync()
    assert res["records_updated"] == 0
    assert res["records_checked"] == 1
    assert called == []  # never touched Cloudflare


def test_sync_complete_dispatch_has_record_context(monkeypatch):
    _add_record("203.0.113.42")
    events = []
    monkeypatch.setattr(integration_engine, "dispatch",
                        lambda event, ctx: events.append((event, ctx)))
    sync_engine.run_sync()

    event, ctx = events[-1]
    assert event == "SYNC_COMPLETE"
    assert ctx["record_name"] == "home.example.com"
    assert ctx["record_type"] == "A"
    assert ctx["zone"] == "example.com"
    assert ctx["records_checked"] == 1
    assert ctx["records_updated"] == 0
    assert ctx["records_unchanged"] == 1
    assert ctx["records"][0]["record_name"] == "home.example.com"


def test_update_success(monkeypatch):
    _add_record("198.51.100.17")
    monkeypatch.setattr(sync_engine.cf, "update_record", lambda *a, **k: {"id": "r1"})
    res = sync_engine.run_sync()
    assert res["records_updated"] == 1
    assert res["records_failed"] == 0
    assert config_store.load()["records"][0]["cloudflare_value"] == "203.0.113.42"


def test_sync_due_skips_before_interval(monkeypatch):
    _add_record("203.0.113.42")
    cfg = config_store.load()
    cfg["sync_interval_minutes"] = 30
    config_store.save(cfg)
    sync_engine.run_sync()

    called = []
    monkeypatch.setattr(sync_engine.cf, "update_record", lambda *a, **k: called.append(1))
    res = sync_engine.run_sync_if_due()

    assert res["status"] == "skipped"
    assert res["ran"] is False
    assert res["due"] is False
    assert called == []


def test_sync_due_runs_after_interval(monkeypatch):
    _add_record("198.51.100.17")
    cfg = config_store.load()
    cfg["sync_interval_minutes"] = 5
    config_store.save(cfg)
    sync_engine.write_state({
        "last_public_ip": "198.51.100.17",
        "last_sync_at": "2026-01-01T00:00:00Z",
        "last_successful_sync_at": "2026-01-01T00:00:00Z",
        "last_error": None,
    })
    monkeypatch.setattr(sync_engine.cf, "update_record", lambda *a, **k: {"id": "r1"})

    res = sync_engine.run_sync_if_due()

    assert res["status"] == "success"
    assert res["ran"] is True
    assert res["records_updated"] == 1


def test_retry_then_fail(monkeypatch):
    _add_record("198.51.100.17")
    attempts = []

    def always_fail(*a, **k):
        attempts.append(1)
        raise CloudflareError("500", retryable=True, status=500)

    monkeypatch.setattr(sync_engine.cf, "update_record", always_fail)
    monkeypatch.setattr(sync_engine.time, "sleep", lambda *_: None)  # no real waiting
    res = sync_engine.run_sync()
    assert res["records_failed"] == 1
    assert len(attempts) == 3  # three tries then give up


def test_non_retryable_stops_immediately(monkeypatch):
    _add_record("198.51.100.17")
    attempts = []

    def bad_token(*a, **k):
        attempts.append(1)
        raise CloudflareError("invalid token", retryable=False, status=403)

    monkeypatch.setattr(sync_engine.cf, "update_record", bad_token)
    monkeypatch.setattr(sync_engine.time, "sleep", lambda *_: None)
    res = sync_engine.run_sync()
    assert res["records_failed"] == 1
    assert len(attempts) == 1  # no retries for terminal errors
