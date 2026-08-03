from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_web_updater_service_allows_sudo_detach():
    service = (ROOT / "systemd" / "dns-syncer.service").read_text()
    installer = (ROOT / "installer" / "install.sh").read_text()

    assert "NoNewPrivileges=false" in service
    assert "NOPASSWD: $APP_DIR/update.sh --detach" in installer
    assert "install -o root -g root -m 0755 \"$SRC/update.sh\"" in installer
