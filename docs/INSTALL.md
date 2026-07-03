# Install guide

DNS Syncer runs on any Debian-based Linux host with `systemd` and Python 3.11+
(Raspberry Pi 3B or newer recommended). No Docker, no database, no Node.js.

## One-command install

```bash
git clone <repo-url> dns-syncer
cd dns-syncer
sudo bash installer/install.sh
```

The installer creates the `dns-syncer` service user, installs the app to
`/opt/dns-syncer`, sets up a virtualenv, installs the systemd units, and starts
the service and timer. When it finishes it prints the local URL.

Everything else — token, zone, records, webhooks — is configured in the web UI.

## Manual install

```bash
sudo useradd --system --home /opt/dns-syncer --shell /usr/sbin/nologin dns-syncer
sudo install -d -o dns-syncer -g dns-syncer /opt/dns-syncer /etc/dns-syncer /var/lib/dns-syncer /var/log/dns-syncer
sudo cp -r backend/app backend/pyproject.toml frontend /opt/dns-syncer/
sudo python3 -m venv /opt/dns-syncer/.venv
sudo /opt/dns-syncer/.venv/bin/pip install /opt/dns-syncer
sudo chown -R dns-syncer:dns-syncer /opt/dns-syncer
sudo cp systemd/* /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now dns-syncer.service dns-syncer.timer
```

## Development install

Runs against `./.local/` instead of the system paths — no root needed.

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
DNS_SYNCER_DEV=1 uvicorn app.main:app --reload --port 5055
```

Open http://localhost:5055. Run tests with `pytest`.

## Uninstall

```bash
sudo bash installer/uninstall.sh
```

It stops and removes the services, deletes `/opt/dns-syncer`, and asks before
removing config, state, and logs (default: keep).
