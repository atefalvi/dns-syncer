"""Non-secret config in config.json, with atomic writes."""
import json
import os
import tempfile

from app import paths
from app.settings import default_config

_cache: dict | None = None


def _atomic_write(path, data: str) -> None:
    paths.ensure_dirs()
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=".tmp-")
    try:
        with os.fdopen(fd, "w") as f:
            f.write(data)
        os.replace(tmp, path)
        try:
            os.chmod(path, 0o640)
        except PermissionError:
            pass
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def load() -> dict:
    global _cache
    if _cache is not None:
        return _cache
    if paths.CONFIG_FILE.exists():
        _cache = json.loads(paths.CONFIG_FILE.read_text())
    else:
        _cache = default_config()
        save(_cache)
    return _cache


def save(cfg: dict) -> None:
    global _cache
    _cache = cfg
    _atomic_write(paths.CONFIG_FILE, json.dumps(cfg, indent=2))


def reset_cache() -> None:
    """Drop the in-memory cache (used by tests and the CLI process)."""
    global _cache
    _cache = None
