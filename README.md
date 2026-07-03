# DNS Syncer — by DataDreamer

A lightweight self-hosted Cloudflare DNS updater with a local web UI, built to
run quietly on a Raspberry Pi alongside your other home-lab services.

It checks your network's public IP on a schedule, updates the Cloudflare DNS
records you select when the IP changes, keeps a full local log, and can notify
any webhook (Discord, Slack, Teams, or generic).

**Fast. Secure. Resource-efficient.** One small Python process serves the API
and static UI; a `systemd` timer runs the sync — no background loop, no
database, no Docker, no Node.js in production.

## What it does

- Detects your public IP (default: ipify).
- Compares it to your selected Cloudflare A/AAAA records and updates on change.
- Retries transient Cloudflare failures 3 times.
- Stores a capped, searchable JSONL log locally.
- Sends outbound webhooks on chosen events.
- Encrypts your Cloudflare token at rest; never shows it in the browser.

## Requirements

- Debian-based Linux with `systemd` (Raspberry Pi 3B+ or any Debian host)
- Python 3.11+
- A Cloudflare API token scoped to one zone (`Zone:Read` + `DNS:Edit`)

## Install

```bash
git clone <repo-url> dns-syncer
cd dns-syncer
sudo bash installer/install.sh
```

Then open `http://<device-ip>:5055`. Full guide: [docs/INSTALL.md](docs/INSTALL.md).

## Configure

Everything is in the web UI:

1. **Settings → Cloudflare** — paste token, Save, Verify, pick zone.
2. **Records → Add Record** — hostname + type (A/AAAA).
3. **Run Sync** (header button).

Token setup: [docs/CLOUDFLARE_TOKEN.md](docs/CLOUDFLARE_TOKEN.md).

## Run manually

From the header **Run Sync**, or on the CLI:

```bash
sudo -u dns-syncer /opt/dns-syncer/.venv/bin/python -m app.cli sync-once
```

Scheduled syncs run every 30 minutes via `dns-syncer.timer` (change the interval
in Settings, then `sudo systemctl restart dns-syncer.timer`).

## Logs

The **Logs** screen shows the full event history with filters, search, detail
view, and CSV export. Logs are capped (default 1000 entries) at
`/var/log/dns-syncer/events.jsonl`.

## Integrations

**Integrations** lets you POST DNS Syncer events to any HTTP endpoint. Pick a
preset (Discord / Slack / Teams / Generic), choose trigger events, edit the body
template with `{{variables}}`, and **Send Test**.

## Security

DNS Syncer stores infrastructure credentials, so it is built to keep them safe:

- **Encrypted at rest** — your Cloudflare token and webhook URLs are encrypted
  with a machine-local Fernet key (`/etc/dns-syncer/secrets.key`, mode `0600`)
  and stored in `/etc/dns-syncer/secrets.enc`. They are never written to
  `config.json`.
- **Never exposed** — the token is never logged and never returned to the
  browser; the UI only shows a masked value like `••••••••••••d3f7`.
- **Least privilege** — runs as a dedicated non-login `dns-syncer` user with a
  hardened unit (`NoNewPrivileges`, `ProtectSystem=full`). Config, state, and
  log directories are `0750`, owned by that user.
- **Scoped token** — use a Cloudflare token limited to a single zone with only
  `Zone:Read` + `DNS:Edit`. If it leaks, revoke it and save a new one.
- **Nothing committed** — `.gitignore` excludes `*.key`, `*.enc`, `.env`,
  `.local/`, and `.claude/`, so secrets and local runtime data stay off git.

> ⚠️ **Trusted networks only.** v1 has no login and binds to `0.0.0.0:5055` by
> default so you can reach it from your LAN. Do **not** port-forward or expose
> it to the public internet. To restrict it to the device itself, set the bind
> host to `127.0.0.1` in **Settings → Local App**.

## Uninstall

```bash
sudo bash installer/uninstall.sh
```

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Development

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
DNS_SYNCER_DEV=1 uvicorn app.main:app --reload --port 5055   # http://localhost:5055
pytest
```

---

DNS Syncer by DataDreamer.
