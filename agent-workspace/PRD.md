# DNS Syncer by DataDreamer — Single-Shot Agent PRD

> **Build target:** A lightweight Raspberry Pi Cloudflare DNS updater with a local web application.
>
> **Product name:** **DNS Syncer**
>
> **Brand line:** **by DataDreamer**
>
> **Repository slug:** `dns-syncer`
>
> **Instruction to coding agent:** This document is the single source of truth. Build the project from this PRD in one pass. Do not create extra planning documents. Do not copy the UI inspiration images exactly. Use them only to understand the desired local-app feel and density. The final UI must follow the DataDreamer Observatory design system.




---

## Golden rule: fast, secure, resource-efficient

This is the most important implementation rule.

DNS Syncer runs on a Raspberry Pi alongside other small home-lab services. It must stay lightweight.

Every technical decision must be judged against:

```text
Fast. Secure. Resource-efficient.
```

### Hard constraints

Do not build anything that violates these constraints:

- No Docker requirement.
- No database server.
- No SQLite for v1 unless absolutely necessary. Prefer local JSON and JSONL files.
- No Node.js runtime in production.
- No React runtime requirement in production.
- No Next.js, Astro, Tailwind, Material UI, shadcn/ui, Redux, or charting library.
- No always-running background sync loop.
- No queue system.
- No Redis.
- No Celery.
- No WebSocket requirement.
- No frequent frontend polling.
- No heavy animations.
- No analytics dashboards.
- No unnecessary dependencies.

### Preferred production shape

Use one small Python service to serve:

1. the local API
2. static frontend files

Use systemd timer for scheduled checks.

The sync engine should only run when:

- the user clicks **Run Sync**
- the systemd timer fires
- the service starts and startup sync is enabled

The app should be mostly idle most of the time.

### Runtime target

On a Raspberry Pi 3B or newer, target:

```text
Idle CPU: near 0%
Idle memory: under 100 MB preferred
Disk writes: minimal
Log storage: capped
Network calls: only on sync/test actions
```

If the implementation is trending heavier than this, simplify it.


---

## 0. Critical naming correction

Use the following names everywhere:

| Context | Required value |
|---|---|
| Product display name | `DNS Syncer` |
| Brand line | `by DataDreamer` |
| Repository / package slug | `dns-syncer` |
| Linux service user | `dns-syncer` |
| App directory | `/opt/dns-syncer` |
| Config directory | `/etc/dns-syncer` |
| State directory | `/var/lib/dns-syncer` |
| Log directory | `/var/log/dns-syncer` |
| Main service | `dns-syncer.service` |
| Sync oneshot service | `dns-syncer-sync.service` |
| Timer | `dns-syncer.timer` |
| Default local API port | `5055` |

Do **not** use:

- `pi-dns-sync`
- `Pi DNS Sync`
- `DNS Thinker`
- `DNS Stinker`
- `DNS Updater`
- `Cloudflare Pi Updater`

The app is called **DNS Syncer by DataDreamer**.

---

## 1. What this project is

DNS Syncer is a small self-hosted application that runs on a Raspberry Pi or any Debian-based Linux host.

It checks the current public IP address of the network, compares it against selected Cloudflare DNS records, updates those records when the IP changes, and keeps a clean local log history.

It must feel like a compact infrastructure application built by DataDreamer.

It is **not** a marketing website.
It is **not** a generic SaaS dashboard.
It is **not** a Pi-hole clone.
It is **not** Docker-first.
It is **not** a heavy observability platform.
It is **not** a monitoring suite.

It is a fast, focused local app.

The user should be able to install it, open a local browser UI, paste a Cloudflare token, select DNS records, run sync, and see logs.

---

## 2. Product goals

### 2.1 Primary goals

1. Run on a Raspberry Pi with low CPU, RAM, and disk usage.
2. Install with a simple shell script.
3. Start automatically on boot using `systemd`.
4. Provide a local browser UI for configuration and monitoring.
5. Detect the current public IP address on a schedule.
6. Update selected Cloudflare DNS records when the public IP changes.
7. Retry failed Cloudflare updates three times.
8. Store complete log history locally.
9. Support generic outbound API/webhook messages.
10. Use DataDreamer branding, colors, spacing, typography, and design discipline.

### 2.2 Secondary goals

1. Keep the code readable enough for a home-lab owner to understand.
2. Keep dependencies minimal.
3. Make logs easy to search, filter, copy, and export.
4. Make the app safe by avoiding token leaks.
5. Design the app so future DNS providers can be added later.
6. Make the frontend feel like an application, not a webpage.

### 2.3 Non-goals for v1

Do not build these in v1:

- Docker deployment
- Kubernetes
- SQLite/Postgres database
- Multi-user accounts
- Cloud-hosted SaaS backend
- OAuth login
- Multi-DNS-provider support
- Full analytics dashboard
- Complex charting
- Mobile native app
- Email server
- MQTT
- Certificate monitoring
- UPS monitoring
- Network monitoring
- Remote access tunneling
- Public internet exposure flow

---

## 3. Brand and design direction

### 3.1 Required brand treatment

The app should present itself as:

```text
DNS Syncer
by DataDreamer
```

Use the DataDreamer logo from:

```text
agent-workspace/assets/brand/datadreamer-logo.svg
```

The DataDreamer Observatory design system is included here:

```text
agent-workspace/assets/reference/datadreamer-observatory-design-system.md
```

Use that design system as the visual authority.

### 3.2 UI inspiration files

The folder below contains inspiration references:

```text
agent-workspace/assets/ui-inspiration/
```

These files are **not final designs** and are **not brand assets**.

They are included only to communicate:

- compact local-app feel
- sidebar layout preference
- log-heavy operational workflow
- density level
- control-panel pattern
- simple settings screens

The coding agent must **not recreate those images exactly**.

The final UI must use:

- DataDreamer Observatory colors
- DataDreamer logo
- dark-only interface
- ember accent
- hairline borders
- compact app panels
- clean sidebar
- clear logs screen

### 3.3 Visual principles

DNS Syncer must feel:

- dark
- compact
- precise
- quiet
- local
- operational
- efficient
- DataDreamer-owned

Avoid:

- green sidebar
- blue-purple SaaS dashboard
- multi-color gradient panels
- marketing hero section
- long scrolling webpage
- generic admin template
- cluttered charts
- fake analytics
- light/dark theme toggle
- overdesigned onboarding wizard

### 3.4 Required color direction

Use the DataDreamer Observatory dark tokens.

Important colors:

```css
--bg-0: #0A0C10;
--bg-1: #0F1318;
--bg-2: #161B22;
--bg-3: #1D242E;
--border-1: #1F262F;
--border-2: #2E3744;
--text-1: #EDEFF3;
--text-2: #A8B1BD;
--text-3: #858E99;
--accent: #FF5C38;
--accent-hover: #FF7657;
--accent-press: #E04A2A;
--accent-subtle: rgba(255,92,56,0.12);
--success: #3ECF8E;
--warning: #F5B83D;
--danger: #F0564A;
--info: #5CA7FF;
```

Use semantic colors only for status indicators. The interface should not become green because status is green.

### 3.5 Typography

Use:

- Inter for UI
- JetBrains Mono for IPs, timestamps, event names, API values, and logs
- Fraunces sparingly for major section headings if needed

Avoid huge editorial page headings. This is an app.

### 3.6 Layout decision

Use a **fixed left sidebar** and **application workspace**.

No marketing navigation.
No homepage.
No light/dark toggle.
No top-level PRD-style webpage sections.

---

## 4. Required repository structure

Create the actual build project like this:

```text
dns-syncer/
├── README.md
├── LICENSE
├── .gitignore
├── .env.example
│
├── agent-workspace/
│   ├── PRD.md
│   └── assets/
│       ├── brand/
│       │   └── datadreamer-logo.svg
│       ├── reference/
│       │   └── datadreamer-observatory-design-system.md
│       └── ui-inspiration/
│           ├── README.md
│           └── reference images
│
├── backend/
│   ├── pyproject.toml
│   ├── README.md
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── settings.py
│   │   ├── paths.py
│   │   ├── models.py
│   │   ├── config_store.py
│   │   ├── secret_store.py
│   │   ├── log_store.py
│   │   ├── ip_provider.py
│   │   ├── cloudflare_client.py
│   │   ├── sync_engine.py
│   │   ├── integration_engine.py
│   │   ├── api.py
│   │   └── cli.py
│   └── tests/
│       ├── test_config_store.py
│       ├── test_log_store.py
│       ├── test_ip_provider.py
│       ├── test_sync_engine.py
│       └── test_api.py
│
├── frontend/
│   ├── index.html
│   ├── styles/
│   │   ├── tokens.css
│   │   ├── base.css
│   │   └── app.css
│   ├── assets/
│   │   └── datadreamer-logo.svg
│   └── js/
│       ├── api.js
│       ├── format.js
│       ├── state.js
│       ├── app.js
│       └── screens/
│           ├── overview.js
│           ├── records.js
│           ├── logs.js
│           ├── integrations.js
│           └── settings.js
│
├── installer/
│   ├── install.sh
│   ├── uninstall.sh
│   └── postinstall.md
│
├── systemd/
│   ├── dns-syncer.service
│   ├── dns-syncer-sync.service
│   └── dns-syncer.timer
│
├── docs/
│   ├── INSTALL.md
│   ├── CLOUDFLARE_TOKEN.md
│   └── TROUBLESHOOTING.md
│
└── scripts/
    ├── dev.sh
    ├── build.sh
    └── lint.sh
```

Do not create multiple PRD documents.
Do not create empty placeholder markdown files.
Only create useful documentation.

---

## 5. Technology stack

### 5.1 Backend

Use Python.

Recommended lean stack:

```text
Python 3.11+
FastAPI or Starlette
Uvicorn
Pydantic
httpx
cryptography
pytest
```

Acceptable simplification:

If FastAPI feels heavier than necessary, use Starlette directly. Do not add a larger framework.

Do not use:

- Django
- Celery
- Redis
- SQLAlchemy
- Postgres
- SQLite for v1
- APScheduler
- large background worker frameworks
- long-running scheduler inside the Python process

### 5.2 Frontend

Use the lightest frontend that can deliver the required app experience.

Preferred v1 frontend:

```text
Static HTML
CSS
Vanilla JavaScript
Inline SVG icons or a tiny local icon set
```

Optional only if needed during development:

```text
Vite for bundling static assets
TypeScript for maintainability
```

Production must not require Node.js.

Do not use:

- React unless the final compiled app is static and the bundle remains small
- Next.js
- Astro
- Tailwind
- Material UI
- Bootstrap
- shadcn/ui
- Redux
- heavy charting libraries
- runtime icon libraries

Reason: this must stay fast, secure, and resource-efficient on a Raspberry Pi.

### 5.3 Storage

Use local files.

Production paths:

```text
/etc/dns-syncer/config.json
/etc/dns-syncer/secrets.key
/etc/dns-syncer/secrets.enc
/var/lib/dns-syncer/state.json
/var/log/dns-syncer/events.jsonl
```

Development fallback paths:

```text
./.local/config.json
./.local/secrets.key
./.local/secrets.enc
./.local/state.json
./.local/events.jsonl
```

### 5.4 Ports

Backend API and static frontend:

```text
0.0.0.0:5055
```

Local app URL:

```text
http://<pi-ip>:5055
```

Preferred v1 approach:

- Build React app into static files.
- Serve static files from FastAPI.
- One process, one port, simple deployment.

---

## 6. Installation flow

### 6.1 Required behavior

The installer must be minimal.

It should not ask for:

- Cloudflare token
- DNS zone
- DNS records
- Discord URL
- webhook details
- check interval

Those belong in the UI.

### 6.2 Installer responsibilities

`installer/install.sh` must:

1. Confirm OS is Linux.
2. Confirm `systemd` exists.
3. Confirm Python 3.11+ or install required Python packages.
4. Create service user:

```text
dns-syncer
```

5. Create directories:

```text
/opt/dns-syncer
/etc/dns-syncer
/var/lib/dns-syncer
/var/log/dns-syncer
```

6. Copy backend files.
7. Copy frontend build files.
8. Create Python virtual environment:

```text
/opt/dns-syncer/.venv
```

9. Install backend dependencies.
10. Copy systemd unit files.
11. Enable and start:

```text
dns-syncer.service
dns-syncer.timer
```

12. Print the local URL:

```text
DNS Syncer installed.

Open:
http://<device-ip>:5055

Configuration happens in the web app.
```

### 6.3 Installer tone

Output should be simple:

```text
DNS Syncer installer

✓ Python detected
✓ systemd detected
✓ Created service user
✓ Installed backend
✓ Installed frontend
✓ Started service
✓ Started timer

Open http://192.168.1.25:5055
```

### 6.4 Uninstaller

`installer/uninstall.sh` must:

1. Stop services.
2. Disable services.
3. Remove systemd files.
4. Ask before deleting config/logs.

Prompt:

```text
Remove configuration and logs? [y/N]
```

Default is no.

---

## 7. systemd architecture

Use two service units and one timer.

### 7.1 Local app service

`dns-syncer.service`

Purpose:

- runs FastAPI backend
- serves frontend
- exposes local API
- does not perform scheduled sync by itself

Example:

```ini
[Unit]
Description=DNS Syncer local web application
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=dns-syncer
Group=dns-syncer
WorkingDirectory=/opt/dns-syncer
ExecStart=/opt/dns-syncer/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 5055
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### 7.2 Sync oneshot service

`dns-syncer-sync.service`

Purpose:

- runs one sync cycle
- exits after completion

Example:

```ini
[Unit]
Description=DNS Syncer DNS update check
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=dns-syncer
Group=dns-syncer
WorkingDirectory=/opt/dns-syncer
ExecStart=/opt/dns-syncer/.venv/bin/python -m app.cli sync-once
```

### 7.3 Timer

`dns-syncer.timer`

Purpose:

- triggers sync service on schedule

Default interval:

```text
30 minutes
```

Example:

```ini
[Unit]
Description=Run DNS Syncer on schedule

[Timer]
OnBootSec=2min
OnUnitActiveSec=30min
Unit=dns-syncer-sync.service
Persistent=true

[Install]
WantedBy=timers.target
```

### 7.4 Interval changes

When user changes sync interval in UI:

1. Update config.
2. Regenerate timer or write override.
3. Run:

```bash
systemctl daemon-reload
systemctl restart dns-syncer.timer
```

If permission handling is too much for v1, save the setting and show:

```text
Restart DNS Syncer for schedule changes to take effect.
```

Prefer automatic update.

---

## 8. Backend architecture

### 8.1 Backend modules

#### `paths.py`

Centralizes file paths.

Must support production and development mode.

#### `models.py`

Defines typed models:

- AppStatus
- RecordConfig
- SyncResult
- LogEntry
- IntegrationConfig
- AppSettings
- CloudflareTokenStatus

#### `config_store.py`

Reads/writes non-secret config.

Must use atomic writes.

#### `secret_store.py`

Handles Cloudflare token and webhook secrets.

Secrets must not be stored in plain config.

Use `cryptography.fernet`.

A generated machine-local key may be stored at:

```text
/etc/dns-syncer/secrets.key
```

Set permissions:

```text
0600
```

#### `log_store.py`

Writes JSON Lines logs and reads paginated/filterable logs.

Log file:

```text
/var/log/dns-syncer/events.jsonl
```

Keep a maximum of 1000 entries by default.

#### `ip_provider.py`

Fetches public IP address.

Default:

```text
https://api.ipify.org
```

Must support timeouts.

Timeout:

```text
8 seconds
```

#### `cloudflare_client.py`

Cloudflare API wrapper.

Responsibilities:

- verify token
- list zones
- list DNS records
- update DNS record
- handle errors
- respect rate limit responses

#### `sync_engine.py`

Main sync logic.

Responsibilities:

1. Load config.
2. Fetch public IP.
3. Load enabled records.
4. Fetch DNS record values from Cloudflare.
5. Compare current DNS value to public IP.
6. Update when changed.
7. Retry failures three times.
8. Log each step.
9. Trigger integrations.

#### `integration_engine.py`

Sends outbound notifications/webhooks.

Supports:

- generic webhook
- Discord webhook
- Slack webhook
- Microsoft Teams webhook

All are wrappers around a generic HTTP sender.

#### `api.py`

FastAPI routes.

#### `main.py`

Creates FastAPI app, mounts static frontend, registers routes.

#### `cli.py`

CLI entry point for systemd oneshot.

Commands:

```bash
python -m app.cli sync-once
python -m app.cli verify-token
python -m app.cli print-status
```

---

## 9. Backend API specification

Base URL:

```text
http://localhost:5055/api
```

### 9.1 Health

```http
GET /api/health
```

Response:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "uptime_seconds": 8300
}
```

### 9.2 Status

```http
GET /api/status
```

Response:

```json
{
  "app_status": "healthy",
  "current_ip": "203.0.113.42",
  "last_sync_at": "2026-07-02T21:20:14Z",
  "next_sync_hint": "30 minutes",
  "records_total": 3,
  "records_ok": 3,
  "token_status": "valid",
  "service_status": "running",
  "timer_status": "active"
}
```

### 9.3 Run sync manually

```http
POST /api/sync/run
```

Response:

```json
{
  "status": "success",
  "started_at": "2026-07-02T21:20:14Z",
  "completed_at": "2026-07-02T21:20:16Z",
  "public_ip": "203.0.113.42",
  "records_checked": 3,
  "records_updated": 2,
  "records_failed": 0
}
```

### 9.4 Records

```http
GET /api/records
POST /api/records
PATCH /api/records/{id}
DELETE /api/records/{id}
```

Record model:

```json
{
  "id": "rec_home_a",
  "enabled": true,
  "zone_id": "cloudflare_zone_id",
  "zone_name": "example.com",
  "record_id": "cloudflare_record_id",
  "hostname": "home",
  "fqdn": "home.example.com",
  "type": "A",
  "proxied": true,
  "target_ip": "203.0.113.42",
  "cloudflare_value": "203.0.113.42",
  "status": "synced",
  "last_checked_at": "2026-07-02T21:20:14Z",
  "last_updated_at": "2026-07-02T21:20:14Z"
}
```

### 9.5 Logs

```http
GET /api/logs?level=INFO&event=RECORD_UPDATED&q=home&page=1&page_size=50
```

Response:

```json
{
  "page": 1,
  "page_size": 50,
  "total": 215,
  "entries": [
    {
      "id": "log_001",
      "timestamp": "2026-07-02T21:20:14Z",
      "level": "INFO",
      "event": "SYNC_COMPLETE",
      "record": null,
      "message": "3 records synced successfully",
      "details": {
        "duration_ms": 1230
      }
    }
  ]
}
```

### 9.6 Settings

```http
GET /api/settings
PATCH /api/settings
```

Settings model:

```json
{
  "sync_interval_minutes": 30,
  "ip_provider": "ipify",
  "log_retention_days": 30,
  "max_log_entries": 1000,
  "run_on_startup": true,
  "cloudflare_zone_id": "zone_id",
  "cloudflare_zone_name": "example.com",
  "ui_bind_host": "0.0.0.0",
  "ui_port": 5055
}
```

### 9.7 Cloudflare token

```http
POST /api/cloudflare/token
POST /api/cloudflare/token/verify
GET /api/cloudflare/zones
GET /api/cloudflare/records?zone_id=...
```

Never return the full token.

Token display format:

```text
••••••••••••d3f7
```

### 9.8 Integrations

```http
GET /api/integrations
POST /api/integrations
PATCH /api/integrations/{id}
DELETE /api/integrations/{id}
POST /api/integrations/{id}/test
```

Integration model:

```json
{
  "id": "int_discord_main",
  "enabled": true,
  "name": "Discord alerts",
  "type": "discord",
  "trigger_events": [
    "SYNC_COMPLETE",
    "SYNC_FAILED",
    "RECORD_UPDATED"
  ],
  "method": "POST",
  "url_secret_ref": "secret_int_discord_main_url",
  "headers": {
    "Content-Type": "application/json"
  },
  "body_template": {
    "content": "DNS Syncer: {{message}}"
  }
}
```

---

## 10. Data model

### 10.1 Config file

Path:

```text
/etc/dns-syncer/config.json
```

Example:

```json
{
  "version": "0.1.0",
  "sync_interval_minutes": 30,
  "ip_provider": {
    "name": "ipify",
    "url": "https://api.ipify.org",
    "type": "ipv4"
  },
  "cloudflare": {
    "selected_zone_id": "",
    "selected_zone_name": ""
  },
  "records": [],
  "integrations": [],
  "logging": {
    "retention_days": 30,
    "max_entries": 1000
  },
  "ui": {
    "host": "0.0.0.0",
    "port": 5055
  }
}
```

### 10.2 Secrets file

Path:

```text
/etc/dns-syncer/secrets.enc
```

Encrypted content contains:

```json
{
  "cloudflare_api_token": "...",
  "integration_urls": {
    "int_123": "https://..."
  },
  "integration_headers": {
    "int_123": {
      "Authorization": "Bearer ..."
    }
  }
}
```

### 10.3 State file

Path:

```text
/var/lib/dns-syncer/state.json
```

Example:

```json
{
  "last_public_ip": "203.0.113.42",
  "last_sync_at": "2026-07-02T21:20:14Z",
  "last_successful_sync_at": "2026-07-02T21:20:14Z",
  "last_error": null
}
```

### 10.4 Log file

Path:

```text
/var/log/dns-syncer/events.jsonl
```

Example lines:

```json
{"id":"log_001","timestamp":"2026-07-02T21:20:14Z","level":"INFO","event":"SYNC_START","message":"Starting sync cycle"}
{"id":"log_002","timestamp":"2026-07-02T21:20:15Z","level":"INFO","event":"IP_DETECTED","message":"Public IP detected","details":{"ip":"203.0.113.42"}}
{"id":"log_003","timestamp":"2026-07-02T21:20:16Z","level":"INFO","event":"RECORD_UPDATED","record":"home.example.com","message":"A record updated","details":{"old_ip":"198.51.100.17","new_ip":"203.0.113.42"}}
```

---

## 11. Sync logic

### 11.1 Manual sync

When user clicks **Run Sync**:

1. Disable button.
2. Show loading state.
3. POST `/api/sync/run`.
4. Backend runs sync immediately.
5. UI updates status, logs, records.
6. Button returns to normal.

### 11.2 Scheduled sync

Systemd timer runs:

```bash
python -m app.cli sync-once
```

### 11.3 Retry logic

For each Cloudflare record update:

- Try once.
- If failed, wait 2 seconds.
- Try second time.
- If failed, wait 5 seconds.
- Try third time.
- If failed, mark record as failed.
- Log final failure.
- Trigger failure integration.

Retry only for:

- network timeout
- 429 rate limit
- 5xx Cloudflare response
- temporary DNS/provider error

Do not retry for:

- invalid token
- missing permission
- record not found
- zone not found
- invalid config

### 11.4 Sync result statuses

Use:

```text
synced
updated
unchanged
failed
paused
unknown
```

### 11.5 Event names

Use uppercase event names:

```text
SYNC_START
SYNC_COMPLETE
SYNC_FAILED
IP_DETECTED
IP_UNCHANGED
RECORD_CHECKED
RECORD_UPDATED
RECORD_UNCHANGED
RECORD_UPDATE_FAILED
TOKEN_VERIFIED
TOKEN_INVALID
INTEGRATION_SENT
INTEGRATION_FAILED
SETTINGS_UPDATED
SERVICE_STARTED
```

---

## 12. Security requirements

### 12.1 Token handling

Never store tokens in:

- frontend localStorage
- plain config JSON
- logs
- browser-visible API responses

Store tokens encrypted in:

```text
/etc/dns-syncer/secrets.enc
```

### 12.2 Token masking

Display only:

```text
••••••••••••d3f7
```

### 12.3 File permissions

Production permissions:

```text
/etc/dns-syncer                  0750
/etc/dns-syncer/config.json      0640
/etc/dns-syncer/secrets.key      0600
/etc/dns-syncer/secrets.enc      0600
/var/log/dns-syncer              0750
/var/log/dns-syncer/events.jsonl 0640
```

Owner:

```text
dns-syncer:dns-syncer
```

### 12.4 Local UI access

For v1, do not add login by default.

Add setting:

```text
Local network only
```

Default bind:

```text
0.0.0.0
```

User may switch to:

```text
127.0.0.1
```

Add a warning in Settings:

```text
This app stores infrastructure credentials. Only expose it on trusted networks.
```

### 12.5 Logs

Never log:

- full Cloudflare token
- webhook secret URLs
- Authorization headers
- secret payload values

---

## 13. Cloudflare requirements

### 13.1 Token permissions

Document minimum Cloudflare token permissions:

```text
Zone:Zone:Read
Zone:DNS:Edit
```

Zone resources:

```text
Include: Specific zone
```

### 13.2 Token verification

Verification should:

1. Call Cloudflare token verify endpoint.
2. Confirm token is valid.
3. Attempt to list zones.
4. Confirm selected zone is visible.
5. Attempt to list DNS records.

### 13.3 Record adding flow

The user should not need to enter Cloudflare record IDs manually.

Flow:

1. User enters/selects zone.
2. User enters hostname.
3. User selects record type: A or AAAA.
4. Backend searches Cloudflare DNS records.
5. If found, store record ID.
6. If not found, ask whether to create it.

For v1:

- support existing records
- creating missing records can be supported if simple
- if not supported, show clear error

### 13.4 Proxied records

Support Cloudflare `proxied` setting.

Record table should show:

```text
Proxied: yes/no
```

If user updates proxied in UI, update Cloudflare record with same content.

---

## 14. Outbound integrations

### 14.1 Principle

Do not pigeonhole the user into one destination.

The app should be able to send a message to any API.

### 14.2 Integration types

v1:

1. Generic Webhook
2. Discord
3. Slack
4. Microsoft Teams

All are HTTP requests.

### 14.3 Trigger events

User can select:

```text
SYNC_COMPLETE
SYNC_FAILED
RECORD_UPDATED
RECORD_UPDATE_FAILED
TOKEN_INVALID
SERVICE_STARTED
```

### 14.4 Template variables

Support:

```text
{{event}}
{{status}}
{{message}}
{{old_ip}}
{{new_ip}}
{{record_name}}
{{record_type}}
{{zone}}
{{timestamp}}
{{duration_ms}}
{{error}}
```

### 14.5 Generic webhook UI

Fields:

- Name
- Enabled
- Trigger events
- Method
- URL
- Headers
- Body template
- Test payload button

### 14.6 Example generic payload

```json
{
  "source": "dns-syncer",
  "product": "DNS Syncer by DataDreamer",
  "event": "{{event}}",
  "message": "{{message}}",
  "old_ip": "{{old_ip}}",
  "new_ip": "{{new_ip}}",
  "record": "{{record_name}}",
  "zone": "{{zone}}",
  "timestamp": "{{timestamp}}"
}
```

### 14.7 Discord payload

```json
{
  "content": "**DNS Syncer**\n{{message}}\n`{{old_ip}} → {{new_ip}}`"
}
```

---

## 15. Frontend product direction

### 15.1 Core design decision

This is an application, not a webpage.

Use:

- fixed sidebar
- fixed header
- content workspace
- compact cards
- clean tables
- dense logs
- minimal motion
- dark-only theme

Do not use:

- marketing hero
- long scrolling homepage
- theme toggle
- green sidebar
- generic SaaS gradients
- large decorative charts
- unnecessary text blocks

### 15.2 Navigation

Sidebar items:

```text
Overview
Records
Logs
Integrations
Settings
```

Do not include separate pages for:

- Token
- API
- System

Token belongs in Settings → Cloudflare.
Outgoing APIs belong in Integrations.
System health belongs in Overview.

### 15.3 Header

Header content:

Left:

```text
DNS Syncer     Healthy
```

Right:

```text
Run Sync
Verify Token
```

### 15.4 Sidebar visual

Sidebar:

- width around 260px
- background `--bg-0`
- right border `--border-1`
- DataDreamer logo top
- active item has ember left border and subtle background
- no green backgrounds
- no big gradients

### 15.5 Sidebar brand block

Use:

```text
[DataDreamer logo]
DNS Syncer
by DataDreamer
```

Bottom:

```text
DNS Syncer
v0.1.0
```

---

## 16. Frontend screens

## 16.1 Overview screen

### Purpose

Answer quickly:

- What is my current public IP?
- Did sync work?
- Which records are managed?
- What happened recently?
- Is the service healthy?

### Layout

```text
┌─────────────────────────────────────────────────────────────┐
│ Header: DNS Syncer  [Healthy]              [Run Sync]        │
├───────────────┬─────────────────────────────────────────────┤
│ Sidebar       │ Stat cards: IP | Last Sync | Records | Token │
│               │                                             │
│               │ Recent Activity        Health Summary        │
│               │                                             │
│               │ Managed Records                             │
└───────────────┴─────────────────────────────────────────────┘
```

### Top cards

1. Current IP
2. Last Sync
3. Records
4. Token

Current IP card:

```text
Current IP
203.0.113.42
Auto-detected
```

Last Sync card:

```text
Last Sync
2m ago
2026-07-02 21:20:14
```

Records card:

```text
Records
3
3 OK
```

Token card:

```text
Token
••••••••d3f7
Valid
```

### Recent Activity

Show last 5 events.

Columns:

- level dot
- event label
- message
- time

### Health Summary

Rows:

```text
Cloudflare API       Connected
Public IP Provider   Available
Systemd Timer        Active
Log Writer           Ready
```

### Managed Records Preview

Show up to 5 records.

Columns:

- Type
- Name
- Value
- Status
- Updated

---

## 16.2 Records screen

### Purpose

Manage DNS records selected for syncing.

### Layout

```text
Records
Manage DNS records synced by DNS Syncer.

[Search records...] [Filter] [Add Record] [Run Sync]

Managed Records Table
Summary rail
```

### Table columns

```text
Enabled
Type
Name
Zone
Current IP
Target IP
Status
Updated
Actions
```

### Row statuses

- Synced
- Updated
- Failed
- Paused
- Unknown

### Add Record flow

Open modal.

Fields:

1. Zone
2. Hostname
3. Type: A / AAAA
4. Proxied toggle
5. Enabled toggle

Buttons:

```text
Cancel
Save Record
```

After saving:

1. backend finds Cloudflare record
2. stores record ID
3. logs `RECORD_ADDED`
4. returns to Records screen

---

## 16.3 Logs screen

### Purpose

Logs are a first-class feature.

The user must be able to understand exactly what happened.

### Layout

```text
Logs

[All] [Sync] [Token] [Integration] [Warnings] [Errors]
[Search logs...] [Export CSV]

Log table                                  Log summary
```

### Table columns

```text
Time
Level
Event
Details
Record
Actions
```

### Level display

Use small colored dot + label.

```text
● INFO
● DEBUG
● WARN
● ERROR
```

### Filters

Required:

- all
- sync
- token
- integrations
- warnings
- errors

Search should match:

- event
- message
- record
- IP address
- timestamp

### Log summary rail

Show:

```text
Total logs
Info
Debug
Warnings
Errors
Retention
Export
```

### Expand log details

Row action opens a drawer or modal.

Show:

- event
- timestamp
- level
- message
- record
- details JSON
- copy JSON button

---

## 16.4 Integrations screen

### Purpose

Allow user to send messages to any API or common notification platform.

### Integration cards

Show cards:

1. Generic Webhook
2. Discord
3. Slack
4. Microsoft Teams

Each card:

```text
Name
Description
Connected / Not connected
Last sent
Configure
Test
```

### Generic Webhook builder

Fields:

```text
Integration Name
Enabled
Trigger Events
Method
URL
Headers
Body Template
```

Actions:

```text
Send Test
Save Integration
```

### Trigger event checkboxes

```text
SYNC_COMPLETE
SYNC_FAILED
RECORD_UPDATED
RECORD_UPDATE_FAILED
TOKEN_INVALID
SERVICE_STARTED
```

### Template helper

Show variables:

```text
{{event}}
{{message}}
{{old_ip}}
{{new_ip}}
{{record_name}}
{{zone}}
{{timestamp}}
```

---

## 16.5 Settings screen

### Purpose

Configure app behavior.

Do not create separate Token page.

Cloudflare token belongs here.

### Sections

1. Sync Behavior
2. Public IP Source
3. Cloudflare
4. Logging
5. Local App
6. Advanced

### Sync Behavior

Fields:

```text
Sync Interval
Run on startup
```

Default interval:

```text
30 minutes
```

Options:

```text
5 minutes
15 minutes
30 minutes
60 minutes
```

### Public IP Source

Fields:

```text
Provider
Custom URL
```

Default:

```text
ipify.org
```

### Cloudflare

Fields:

```text
API Token
Verify Token
Selected Zone
Refresh Zones
```

Token field:

- password style
- reveal button
- save button
- verify button
- status badge

### Logging

Fields:

```text
Max entries
Retention days
Export logs
Clear logs
```

Default:

```text
1000 entries
30 days
```

### Local App

Fields:

```text
Bind host
Port
```

### Advanced

Fields:

```text
Custom user agent
Retry attempts
Retry delay
```

Defaults:

```text
retry attempts: 3
retry delays: 2s, 5s
```

---

## 17. Frontend components

Build small reusable frontend functions/components using vanilla JavaScript and CSS. Keep the implementation simple. Do not introduce a frontend framework unless absolutely necessary.

### 17.1 AppShell

Implement as static HTML shell plus JavaScript screen router.

Includes:

- sidebar
- header
- main content

### 17.2 Sidebar

Items:

```ts
[
  { id: "overview", label: "Overview", icon: Grid },
  { id: "records", label: "Records", icon: Database },
  { id: "logs", label: "Logs", icon: FileText },
  { id: "integrations", label: "Integrations", icon: Workflow },
  { id: "settings", label: "Settings", icon: Settings }
]
```

### 17.3 HeaderBar

Shows:

- app name
- health status
- primary actions

### 17.4 Card

Simple bordered surface.

No heavy shadows.

### 17.5 StatusPill

Variants:

```ts
"success" | "warning" | "danger" | "info" | "neutral"
```

### 17.6 LogTable

Must support:

- loading
- empty
- pagination
- filter
- search
- row details

### 17.7 Modal

Used for:

- Add Record
- Configure Integration
- Log Details
- Clear Logs Confirmation

---

## 18. Responsive design

### 18.1 Desktop first

Target local app usage on desktop/laptop.

Minimum good width:

```text
1280px
```

### 18.2 Tablet

At widths below 1024px:

- sidebar collapses to icon rail
- content becomes single column
- summary rails move below main content

### 18.3 Mobile

Basic support only.

At widths below 768px:

- sidebar becomes top menu or drawer
- tables become horizontally scrollable
- logs remain usable

Do not over-optimize mobile in v1.

---

## 19. README requirements

Create a practical README.

Include:

1. What it does
2. Requirements
3. Install
4. Configure
5. Cloudflare token setup
6. Run manually
7. Logs
8. Integrations
9. Uninstall
10. Troubleshooting

Do not write marketing fluff.

---

## 20. Documentation requirements

Create only useful docs.

### `docs/INSTALL.md`

Include:

- one-command install
- manual install
- development install
- uninstall

### `docs/CLOUDFLARE_TOKEN.md`

Include:

- how to create Cloudflare token
- required permissions
- zone restrictions
- security notes

### `docs/TROUBLESHOOTING.md`

Include:

Common issues:

- token invalid
- zone not visible
- record not found
- IP provider timeout
- Cloudflare rate limit
- systemd timer not running
- UI not reachable
- permission denied

---

## 21. Testing requirements

### 21.1 Backend tests

Required tests:

- config read/write
- secret encryption/decryption
- log append/read/filter
- IP provider success/failure
- Cloudflare client mocked success/failure
- sync no-change
- sync update success
- sync update retry failure
- integration send success/failure
- API health/status

### 21.2 Frontend tests

Optional for v1 but structure code cleanly.

At minimum:

- TypeScript passes
- build succeeds
- no console errors in main flows

### 21.3 Manual QA checklist

Before completion:

- fresh install works
- UI loads
- token can be saved
- token can be verified
- zone can be selected
- record can be added
- manual sync works
- scheduled sync works
- logs show sync
- failed update logs error
- webhook test sends payload
- uninstall works

---

## 22. Development workflow

### 22.1 Local backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 5055
```

### 22.2 Local frontend

Preferred v1 frontend has no build step.

Open through backend:

```bash
uvicorn app.main:app --reload --port 5055
```

If the agent chooses optional Vite/TypeScript for maintainability, the final production output must be static files only and Node.js must not run on the Pi.

### 22.3 Build frontend

Preferred:

```text
No build required.
```

Optional:

```bash
cd frontend
npm install
npm run build
```

Only use optional build tooling if it does not complicate installation or runtime.

---

## 23. Suggested implementation order

The agent should build in this order.

### Step 1 — Project scaffold

Create files and folders exactly as specified.

### Step 2 — Backend models and storage

Build:

- paths
- models
- config store
- secret store
- log store

### Step 3 — Backend services

Build:

- IP provider
- Cloudflare client
- sync engine
- integration engine

### Step 4 — Backend API

Build FastAPI endpoints.

### Step 5 — Frontend app shell

Build:

- tokens
- base styles
- shell
- sidebar
- header
- cards
- table primitives

### Step 6 — Frontend screens

Build:

1. Overview
2. Records
3. Logs
4. Integrations
5. Settings

### Step 7 — Installer and systemd

Build:

- install.sh
- uninstall.sh
- service units
- timer

### Step 8 — Tests

Add backend tests.

### Step 9 — Documentation

Write README and docs.

### Step 10 — Final QA

Run through checklist.



---

## 24. Resource efficiency requirements

### 24.1 Backend runtime

The backend must be one small process.

It should:

- serve static frontend files
- expose local API endpoints
- stay idle between requests
- not run an internal scheduler loop
- not continuously poll Cloudflare
- not continuously poll the IP provider

### 24.2 Sync runtime

The sync operation should be short-lived.

Triggered by:

- systemd timer
- manual UI action
- optional startup check

Default sync interval:

```text
30 minutes
```

This means 48 checks per day by default.

### 24.3 Logs

Logs must be capped.

Default:

```text
1000 entries
```

At 30-minute intervals, this gives about:

```text
20.8 days of check history
```

Do not let logs grow forever.

### 24.4 Frontend runtime

The frontend should:

- load quickly
- use no charting library
- use no external CDN
- use no heavy JS framework by default
- refresh data only when needed
- avoid aggressive polling

Suggested refresh behavior:

```text
Overview: refresh every 30 seconds only while open
Logs: refresh on screen open and manual refresh
Records: refresh on screen open and after sync
Settings: refresh on screen open
```

### 24.5 Network calls

Avoid unnecessary network calls.

The app should call:

- public IP provider only during sync
- Cloudflare only during token verify, zone/record refresh, or sync
- integrations only during test or selected trigger events

### 24.6 Security and performance tradeoff

Do not weaken token handling for speed.

Token encryption stays required.

Do not store secrets in frontend storage.


---

## 25. Completion definition

The project is complete when the user can:

1. Clone the repo.
2. Run the installer on a Raspberry Pi.
3. Open the local app.
4. Add Cloudflare token in Settings.
5. Verify token.
6. Select zone.
7. Add DNS record.
8. Click Run Sync.
9. See record updated.
10. See logs.
11. Add a generic webhook.
12. Send test payload.
13. Let systemd run scheduled sync automatically.
14. Reboot Pi and confirm app starts again.

---

## 26. Final instruction to agent

Build the simplest complete version that satisfies this PRD while obeying the golden rule: fast, secure, and resource-efficient.

Prefer working software over elaborate architecture.

Use the UI inspiration files only to understand layout density and local-app feel. Do not copy them directly. The actual design must be DataDreamer Observatory.

Do not add unnecessary pages.

Do not add placeholder docs.

Do not over-engineer.

Do not make the installer ask questions that belong in the UI.

Build the project so the user can run it on a Raspberry Pi and understand what happened from the logs.
