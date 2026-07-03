import httpx
import pytest

from app import ip_provider


def test_success(monkeypatch):
    resp = httpx.Response(200, text="203.0.113.42\n",
                          request=httpx.Request("GET", "https://api.ipify.org"))
    monkeypatch.setattr(httpx, "get", lambda *a, **k: resp)
    assert ip_provider.get_public_ip() == "203.0.113.42"


def test_timeout_raises(monkeypatch):
    def boom(*a, **k):
        raise httpx.TimeoutException("timeout")
    monkeypatch.setattr(httpx, "get", boom)
    with pytest.raises(httpx.TimeoutException):
        ip_provider.get_public_ip()
