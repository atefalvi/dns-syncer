from app import config_store, log_store


def test_append_read_filter():
    log_store.append("INFO", "SYNC_START", "start")
    log_store.append("ERROR", "RECORD_UPDATE_FAILED", "boom", record="home.example.com")
    log_store.append("WARN", "TOKEN_INVALID", "bad token")

    assert log_store.query()["total"] == 3
    assert log_store.query(filter_tab="errors")["total"] == 1
    assert log_store.query(filter_tab="token")["total"] == 1
    assert log_store.query(q="home")["total"] == 1
    assert log_store.counts()["ERROR"] == 1


def test_trim_caps_entries():
    cfg = config_store.load()
    cfg["logging"]["max_entries"] = 5
    config_store.save(cfg)
    for i in range(12):
        log_store.append("INFO", "RECORD_CHECKED", f"msg {i}")
    res = log_store.query(page_size=50)
    assert res["total"] == 5
    # newest first
    assert res["entries"][0]["message"] == "msg 11"


def test_csv_export():
    log_store.append("INFO", "SYNC_COMPLETE", "done")
    csv = log_store.as_csv()
    assert "SYNC_COMPLETE" in csv and "timestamp" in csv
