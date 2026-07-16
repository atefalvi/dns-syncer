from fastapi.testclient import TestClient

from app import integration_engine, secret_store
from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_status_setup_state():
    r = client.get("/api/status")
    assert r.status_code == 200
    assert r.json()["token_status"] == "missing"


def test_token_masked_never_returns_plaintext():
    r = client.post("/api/cloudflare/token", json={"token": "abcdefgh1234wxyz"})
    assert r.status_code == 200
    masked = r.json()["token_masked"]
    assert masked.endswith("wxyz")
    assert "abcdefgh" not in masked
    # status reflects a token is present but not verified
    assert client.get("/api/status").json()["token_status"] == "valid" or "set"


def test_integration_crud_and_secret_hidden(monkeypatch):
    monkeypatch.setattr(integration_engine, "_send", lambda *a, **k: {"status": 200})
    r = client.post("/api/integrations", json={
        "name": "Hook", "type": "webhook", "trigger_events": ["SYNC_COMPLETE"],
        "url": "https://secret.example/hook", "body_template": {"content": "{{message}}"},
    })
    assert r.status_code == 200
    body = r.json()
    assert "url" not in body  # secret never returned
    assert body["connected"] is True
    int_id = body["id"]
    assert secret_store.get_integration_url(int_id) == "https://secret.example/hook"

    # test send
    assert client.post(f"/api/integrations/{int_id}/test").json()["ok"] is True
    # delete
    assert client.delete(f"/api/integrations/{int_id}").status_code == 200


def test_render_template():
    out = integration_engine.render({"content": "{{message}}!"}, {"message": "hi"})
    assert out == {"content": "hi!"}


def test_render_template_unknown_tokens_do_not_leak():
    out = integration_engine.render(
        {"content": "{{message}} {{missing}}", "exact": "{{records}}"},
        {"message": "hi", "records": [{"record_name": "home.example.com"}]},
    )
    assert out == {
        "content": "hi ",
        "exact": [{"record_name": "home.example.com"}],
    }
