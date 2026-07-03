"""Thin Cloudflare API wrapper.

Raises CloudflareError with `retryable` set so the sync engine knows whether a
failure is worth retrying (network/429/5xx) or terminal (bad token, 404).
"""
import httpx

from app import config_store, secret_store
from app.settings import CLOUDFLARE_API, HTTP_TIMEOUT, USER_AGENT


class CloudflareError(Exception):
    def __init__(self, message: str, retryable: bool = False, status: int | None = None):
        super().__init__(message)
        self.message = message
        self.retryable = retryable
        self.status = status


def _headers(token: str | None = None) -> dict:
    token = token or secret_store.get_token()
    ua = config_store.load().get("advanced", {}).get("user_agent", USER_AGENT)
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json",
            "User-Agent": ua}


def _request(method: str, path: str, token: str | None = None, **kw) -> dict:
    url = f"{CLOUDFLARE_API}{path}"
    try:
        resp = httpx.request(method, url, headers=_headers(token),
                             timeout=HTTP_TIMEOUT, **kw)
    except httpx.RequestError as e:
        raise CloudflareError(f"Network error: {e}", retryable=True) from e

    if resp.status_code == 429 or resp.status_code >= 500:
        raise CloudflareError(f"Cloudflare {resp.status_code}", retryable=True,
                              status=resp.status_code)
    try:
        data = resp.json()
    except ValueError:
        raise CloudflareError(f"Bad response ({resp.status_code})", status=resp.status_code)

    if not data.get("success", False):
        errs = data.get("errors", [])
        msg = errs[0].get("message") if errs else f"HTTP {resp.status_code}"
        raise CloudflareError(msg, retryable=False, status=resp.status_code)
    return data


def verify_token(token: str | None = None) -> dict:
    """Return {'valid': bool, 'message': str}."""
    try:
        data = _request("GET", "/user/tokens/verify", token=token)
        status = data.get("result", {}).get("status")
        return {"valid": status == "active", "message": status or "unknown"}
    except CloudflareError as e:
        return {"valid": False, "message": e.message}


def list_zones(token: str | None = None) -> list[dict]:
    data = _request("GET", "/zones?per_page=50", token=token)
    return [{"id": z["id"], "name": z["name"]} for z in data.get("result", [])]


def list_records(zone_id: str, name: str | None = None, rtype: str | None = None) -> list[dict]:
    query = "?per_page=100"
    if name:
        query += f"&name={name}"
    if rtype:
        query += f"&type={rtype}"
    data = _request("GET", f"/zones/{zone_id}/dns_records{query}")
    return data.get("result", [])


def find_record(zone_id: str, fqdn: str, rtype: str) -> dict | None:
    for r in list_records(zone_id, name=fqdn, rtype=rtype):
        if r.get("name") == fqdn and r.get("type") == rtype:
            return r
    return None


def update_record(zone_id: str, record_id: str, name: str, rtype: str,
                  content: str, proxied: bool) -> dict:
    body = {"type": rtype, "name": name, "content": content, "proxied": proxied}
    data = _request("PUT", f"/zones/{zone_id}/dns_records/{record_id}", json=body)
    return data["result"]


def create_record(zone_id: str, name: str, rtype: str, content: str, proxied: bool) -> dict:
    body = {"type": rtype, "name": name, "content": content, "proxied": proxied}
    data = _request("POST", f"/zones/{zone_id}/dns_records", json=body)
    return data["result"]
