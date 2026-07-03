"""Fetch the network's current public IP."""
import httpx

from app import config_store
from app.settings import DEFAULT_IP_URL, IP_TIMEOUT, USER_AGENT


def get_public_ip() -> str:
    """Return the public IP as a string. Raises on network/timeout error."""
    cfg = config_store.load()
    url = cfg.get("ip_provider", {}).get("url") or DEFAULT_IP_URL
    ua = cfg.get("advanced", {}).get("user_agent", USER_AGENT)
    resp = httpx.get(url, timeout=IP_TIMEOUT, headers={"User-Agent": ua})
    resp.raise_for_status()
    return resp.text.strip()
