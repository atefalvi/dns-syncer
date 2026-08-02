# After installing DNS Syncer

1. Open `http://<device-ip>:5055` in a browser on your local network.
2. Go to **Settings → Cloudflare**, paste your API token, and click **Save Token** then **Verify Token**.
3. Click **Refresh** to load your zones, select one, and **Save Settings**.
4. Go to **Records → Add Record**, enter a hostname (e.g. `home`), and save.
5. Click **Run Sync**. Check **Logs** to confirm the update.

Scheduled syncs run automatically based on **Settings → Sync Behavior**. The
systemd timer wakes DNS Syncer once per minute, and DNS Syncer only performs a
DNS check when the configured interval is due. The web service also has a
fallback due checker, so automatic syncs continue if the timer is missed while
the app is running.

Interval changes apply automatically; no `systemctl restart` is required.
