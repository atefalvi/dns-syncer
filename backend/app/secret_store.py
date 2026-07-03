"""Encrypted secrets (Cloudflare token, integration URLs/headers).

Fernet key lives at secrets.key (0600); ciphertext at secrets.enc (0600).
Plaintext is a JSON blob; never written unencrypted, never logged.
"""
import json
import os

from cryptography.fernet import Fernet

from app import paths

_EMPTY = {"cloudflare_api_token": "", "integration_urls": {}, "integration_headers": {}}


def _key() -> Fernet:
    paths.ensure_dirs()
    if not paths.SECRETS_KEY_FILE.exists():
        paths.SECRETS_KEY_FILE.write_bytes(Fernet.generate_key())
        try:
            os.chmod(paths.SECRETS_KEY_FILE, 0o600)
        except PermissionError:
            pass
    return Fernet(paths.SECRETS_KEY_FILE.read_bytes())


def _load() -> dict:
    if not paths.SECRETS_ENC_FILE.exists():
        return dict(_EMPTY)
    data = _key().decrypt(paths.SECRETS_ENC_FILE.read_bytes())
    return {**_EMPTY, **json.loads(data)}


def _save(secrets: dict) -> None:
    blob = _key().encrypt(json.dumps(secrets).encode())
    paths.SECRETS_ENC_FILE.write_bytes(blob)
    try:
        os.chmod(paths.SECRETS_ENC_FILE, 0o600)
    except PermissionError:
        pass


# --- Cloudflare token ---

def set_token(token: str) -> None:
    s = _load()
    s["cloudflare_api_token"] = token
    _save(s)


def get_token() -> str:
    return _load().get("cloudflare_api_token", "")


def token_masked() -> str:
    tok = get_token()
    if not tok:
        return ""
    return "•" * 12 + tok[-4:]


# --- Integration secrets ---

def set_integration_secrets(int_id: str, url: str, headers: dict | None) -> None:
    s = _load()
    if url:
        s["integration_urls"][int_id] = url
    if headers is not None:
        s["integration_headers"][int_id] = headers
    _save(s)


def get_integration_url(int_id: str) -> str:
    return _load()["integration_urls"].get(int_id, "")


def get_integration_headers(int_id: str) -> dict:
    return _load()["integration_headers"].get(int_id, {})


def delete_integration(int_id: str) -> None:
    s = _load()
    s["integration_urls"].pop(int_id, None)
    s["integration_headers"].pop(int_id, None)
    _save(s)
