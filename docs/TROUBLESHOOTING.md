# Troubleshooting

Check logs first — the **Logs** screen (and `journalctl`) explain almost every
issue.

```bash
journalctl -u dns-syncer.service -n 50        # web app
journalctl -u dns-syncer-sync.service -n 50   # scheduled sync
```

| Symptom | Cause & fix |
|---|---|
| **Token invalid** | Token expired, revoked, or wrong permissions. Recreate with `Zone:Read` + `DNS:Edit` (see CLOUDFLARE_TOKEN.md) and re-save in Settings. |
| **Zone not visible** | Token isn't scoped to that zone. Edit the token's Zone Resources to include it, or create a new token. Click **Refresh** in Settings. |
| **Record not found** | The hostname doesn't exist in Cloudflare. DNS Syncer creates missing A/AAAA records automatically if the token allows it; otherwise create it in Cloudflare first. Use `@` for the zone root. |
| **IP provider timeout** | No internet or the provider is down. Default is `https://api.ipify.org` (8s timeout). Try another provider URL in Settings → Public IP Source. |
| **Cloudflare rate limit (429)** | Transient. Sync retries automatically (3 attempts). If persistent, increase the sync interval. |
| **Timer not running** | `systemctl status dns-syncer.timer`. Enable with `sudo systemctl enable --now dns-syncer.timer`. Check `systemctl list-timers dns-syncer.timer`. |
| **UI not reachable** | `systemctl status dns-syncer.service`. Confirm the bind host/port (Settings → Local App). If bound to `127.0.0.1` it's only reachable from the Pi itself. Check a firewall isn't blocking port 5055. |
| **Permission denied** | Files under `/etc/dns-syncer` and `/var/log/dns-syncer` must be owned by `dns-syncer:dns-syncer`. Re-run the installer or `chown -R dns-syncer:dns-syncer` those paths. |
| **Schedule change ignored** | The UI stores the interval, but the timer is defined in the unit file. After changing it, run `sudo systemctl restart dns-syncer.timer`. |

## Manual checks from the CLI

```bash
sudo -u dns-syncer /opt/dns-syncer/.venv/bin/python -m app.cli verify-token
sudo -u dns-syncer /opt/dns-syncer/.venv/bin/python -m app.cli sync-once
sudo -u dns-syncer /opt/dns-syncer/.venv/bin/python -m app.cli print-status
```

## Reboot recovery

Both units are enabled for boot: `dns-syncer.service` (`multi-user.target`) and
`dns-syncer.timer` (`timers.target`). After a reboot the web app comes back up
and the timer resumes; `Persistent=true` runs a catch-up sync if one was missed.
