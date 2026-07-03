from app import config_store, secret_store


def test_config_defaults_and_roundtrip():
    cfg = config_store.load()
    assert cfg["sync_interval_minutes"] == 30
    cfg["sync_interval_minutes"] = 15
    config_store.save(cfg)
    config_store.reset_cache()
    assert config_store.load()["sync_interval_minutes"] == 15


def test_secret_encryption_roundtrip_and_masking():
    secret_store.set_token("cf_secret_token_d3f7")
    assert secret_store.get_token() == "cf_secret_token_d3f7"
    masked = secret_store.token_masked()
    assert masked.endswith("d3f7")
    assert "secret" not in masked
    # ciphertext on disk must not contain the plaintext token
    from app import paths
    assert b"cf_secret_token" not in paths.SECRETS_ENC_FILE.read_bytes()


def test_integration_secrets():
    secret_store.set_integration_secrets("int_1", "https://hook", {"X": "1"})
    assert secret_store.get_integration_url("int_1") == "https://hook"
    assert secret_store.get_integration_headers("int_1") == {"X": "1"}
    secret_store.delete_integration("int_1")
    assert secret_store.get_integration_url("int_1") == ""
