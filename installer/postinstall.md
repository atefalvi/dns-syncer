# After installing DNS Syncer

1. Open `http://<device-ip>:5055` in a browser on your local network.
2. Go to **Settings → Cloudflare**, paste your API token, and click **Save Token** then **Verify Token**.
3. Click **Refresh** to load your zones, select one, and **Save Settings**.
4. Go to **Records → Add Record**, enter a hostname (e.g. `home`), and save.
5. Click **Run Sync**. Check **Logs** to confirm the update.

Scheduled syncs run every 30 minutes via `dns-syncer.timer`.

Change the interval in **Settings → Sync Behavior**, then apply it with:

```bash
sudo systemctl restart dns-syncer.timer
```

(The timer interval is defined in `/etc/systemd/system/dns-syncer.timer`; edit
`OnUnitActiveSec` there if you need a value other than the four UI presets.)
