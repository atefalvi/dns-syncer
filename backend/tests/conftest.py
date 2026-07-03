"""Point every store at a throwaway temp dir before app modules load."""
import os
import tempfile

os.environ["DNS_SYNCER_DEV"] = "1"
os.environ["DNS_SYNCER_HOME"] = tempfile.mkdtemp(prefix="dns-syncer-test-")

import pytest

from app import config_store


@pytest.fixture(autouse=True)
def _fresh(tmp_path, monkeypatch):
    # Give each test its own directory so files never collide.
    from app import paths
    for attr, name in [("CONFIG_FILE", "config.json"), ("SECRETS_KEY_FILE", "secrets.key"),
                       ("SECRETS_ENC_FILE", "secrets.enc"), ("STATE_FILE", "state.json"),
                       ("LOG_FILE", "events.jsonl")]:
        monkeypatch.setattr(paths, attr, tmp_path / name)
    monkeypatch.setattr(paths, "CONFIG_DIR", tmp_path)
    monkeypatch.setattr(paths, "STATE_DIR", tmp_path)
    monkeypatch.setattr(paths, "LOG_DIR", tmp_path)
    config_store.reset_cache()
    yield
    config_store.reset_cache()
