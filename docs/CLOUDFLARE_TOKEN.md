# Cloudflare API token

DNS Syncer needs a scoped Cloudflare API token to read your zones and edit DNS
records. It never needs your Cloudflare password or Global API Key.

## Create the token

1. Go to **Cloudflare Dashboard → My Profile → API Tokens → Create Token**.
2. Use **Create Custom Token**.
3. Set these permissions:

   ```
   Zone → Zone → Read
   Zone → DNS  → Edit
   ```

4. Zone Resources:

   ```
   Include → Specific zone → <your domain>
   ```

5. Create the token and copy it. Cloudflare shows it only once.

## Add it to DNS Syncer

1. Open the web UI → **Settings → Cloudflare**.
2. Paste the token and click **Save Token**.
3. Click **Verify Token**. A green **Valid** badge means it works.
4. Click **Refresh** next to Selected Zone, pick your zone, and **Save Settings**.

## What verification checks

- The token is active (Cloudflare verify endpoint).
- Your zones can be listed.
- DNS records in the selected zone can be listed.

## Security notes

- The token is encrypted at rest with a machine-local key
  (`/etc/dns-syncer/secrets.key`, mode `0600`) and stored in
  `/etc/dns-syncer/secrets.enc`.
- It is never written to `config.json`, never logged, and never returned to the
  browser — the UI only ever shows a masked value like `••••••••••••d3f7`.
- Scope the token to a single zone. If it leaks, revoke it in the Cloudflare
  dashboard and save a new one.
