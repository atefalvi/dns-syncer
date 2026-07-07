<div align="center">

# DNS Syncer

**by DataDreamer**

A lightweight, self-hosted Cloudflare DNS updater with a local web UI —
built to run quietly on a Raspberry Pi alongside your other home-lab services.

![Version](https://img.shields.io/badge/version-0.2.1-FF5C38)
![Python](https://img.shields.io/badge/python-3.11%2B-3ECF8E)
![License](https://img.shields.io/badge/license-MIT-5CA7FF)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%20%7C%20Debian-A8B1BD)

*Fast. Secure. Resource-efficient.*

</div>

---

## Table of contents

- [What it does](#what-it-does)
- [Features](#features)
- [Requirements](#requirements)
- [Quick start](#quick-start)
- [Configuration](#configuration)
- [Updating](#updating)
- [Scheduled sync](#scheduled-sync)
- [Logs](#logs)
- [Integrations](#integrations)
- [Security](#security)
- [Uninstall](#uninstall)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

## What it does

Your home network's public IP changes; your Cloudflare DNS records don't.
DNS Syncer fixes that:

1. Detects your current public IP on a schedule (default: every 30 minutes).
2. Compares it to the Cloudflare A/AAAA records you select.
3. Updates the records when the IP changes — with automatic retries.
4. Logs everything locally and can notify any webhook.

**Design goals:** one small Python process serves the API and static UI; a
`systemd` timer runs the sync. No background loop, no database, no Docker,
no Node.js in production. Idle CPU near 0%, memory well under 100 MB.

## Features

| | |
|---|---|
| 🖥️ **Local web UI** | Dark, compact control panel at `http://<pi>:5055` — Overview, Records, Logs, Integrations, Settings |
| 🔄 **Auto sync** | `systemd` timer checks every 30 min (configurable: 5/15/30/60) with catch-up after downtime |
| 🔁 **Smart retries** | Transient failures (timeouts, 429, 5xx) retried 3× ; terminal errors (bad token) fail fast |
| 🔐 **Encrypted secrets** | Cloudflare token and webhook URLs encrypted at rest, never logged, never sent to the browser |
| 📜 **Full log history** | Searchable, filterable, exportable (CSV), capped at 1000 entries |
| 🔔 **Webhooks** | Discord, Slack, Teams, or any HTTP endpoint with `{{template}}` variables |
| ⬆️ **One-click updates** | Update from GitHub releases via the UI or `sudo update.sh` |
| 🪶 **Tiny footprint** | Static HTML/CSS/vanilla JS frontend, files-only storage, no external CDNs |

## Requirements

- Raspberry Pi 3B+ (or any Debian-based Linux host) with `systemd`
- Python 3.11+
- A Cloudflare account and API token scoped to one zone
  (`Zone:Read` + `DNS:Edit` — see [docs/CLOUDFLARE_TOKEN.md](docs/CLOUDFLARE_TOKEN.md))

## Quick start

```bash
git clone https://github.com/atefalvi/dns-syncer.git
cd dns-syncer
sudo bash installer/install.sh
```

Then open `http://<device-ip>:5055` and follow the **Get started** banner:

1. **Settings → Cloudflare** — paste your API token → **Save Token** → **Verify Token**
2. **Refresh** zones → select your zone → **Save Settings**
3. **Records → Add Record** — hostname (e.g. `home`, or `@` for the root) + type
4. Click **Run Sync** — done.

Full install options (manual, development): [docs/INSTALL.md](docs/INSTALL.md)

## Configuration

Everything is configured in the web UI — the installer asks no questions.

| Setting | Where | Default |
|---|---|---|
| Cloudflare token & zone | Settings → Cloudflare | — |
| Sync interval | Settings → Sync Behavior | 30 min |
| Public IP provider | Settings → Public IP Source | ipify.org |
| Log cap / retention | Settings → Logging | 1000 entries / 30 days |
| Bind host / port | Settings → Local App | `0.0.0.0:5055` |

Config lives in `/etc/dns-syncer/config.json`; secrets are encrypted in
`/etc/dns-syncer/secrets.enc`.

## Updating

**From the UI:** Settings → **About & Updates** → *Check for Updates* → *Update Now*.

**From the shell:**

```bash
sudo /opt/dns-syncer/update.sh
```

Either way, the latest GitHub release is downloaded, reinstalled, and the
service restarts. Your config, token, records, and logs are preserved.

## Scheduled sync

Sync runs as a short-lived `systemd` oneshot — the app itself never polls.

```bash
systemctl list-timers dns-syncer.timer     # next run
journalctl -u dns-syncer-sync.service -n 20  # last sync output
```

After changing the interval in Settings: `sudo systemctl restart dns-syncer.timer`.

## Logs

The **Logs** screen shows every event (sync, token, integrations) with
level filters, search, expandable JSON details, and CSV export. Stored at
`/var/log/dns-syncer/events.jsonl`, automatically capped.

## Integrations

Send events (`SYNC_COMPLETE`, `SYNC_FAILED`, `RECORD_UPDATED`, …) to any HTTP
endpoint. Presets for **Discord**, **Slack**, and **Microsoft Teams**, or build
a generic webhook with custom method, headers, and a JSON body template:

```json
{ "content": "**DNS Syncer**\n{{message}}\n`{{old_ip}} → {{new_ip}}`" }
```

Every integration has a **Test** button.

## Security

- **Encrypted at rest** — token and webhook URLs are encrypted with a
  machine-local key (`secrets.key`, mode `0600`); never written to plain config.
- **Never exposed** — secrets are never logged and never returned to the
  browser; the UI shows only a masked value (`••••••••••••d3f7`).
- **Least privilege** — runs as a dedicated non-login `dns-syncer` user with
  `NoNewPrivileges` and `ProtectSystem=full`. The only sudo grant is the exact
  root-owned updater command.
- **Scoped token** — use a single-zone token with `Zone:Read` + `DNS:Edit` only.
- **Nothing committed** — `.gitignore` excludes keys, secrets, env files, and
  local runtime data.

> ⚠️ **Trusted networks only.** v1 has no login and binds to `0.0.0.0:5055` so
> it's reachable from your LAN. Never port-forward it to the internet. To lock
> it to the device itself, set bind host to `127.0.0.1` in Settings → Local App.

## Uninstall

```bash
sudo bash installer/uninstall.sh
```

Stops and removes the services and app. Asks before deleting config and logs
(default: keep).

## Troubleshooting

Common issues (invalid token, zone not visible, timer not running, UI
unreachable, …) are covered in [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

Quick health check:

```bash
systemctl status dns-syncer.service dns-syncer.timer
sudo -u dns-syncer /opt/dns-syncer/.venv/bin/python -m app.cli print-status
```

## Development

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
DNS_SYNCER_DEV=1 uvicorn app.main:app --reload --port 5055   # http://localhost:5055
pytest                                                        # 17 tests
```

Dev mode stores everything under `backend/.local/` — no root, no systemd needed.

## License

[MIT](LICENSE) © DataDreamer
