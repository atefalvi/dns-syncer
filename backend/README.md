# DNS Syncer backend

One small FastAPI app that serves the local API and the static frontend, plus a
CLI used by the `systemd` sync timer. Storage is plain files — no database.

## Layout

| Module | Role |
|---|---|
| `paths.py` | Production (`/etc`, `/var`) vs dev (`./.local`) file paths |
| `settings.py` | Constants and default config |
| `models.py` | Pydantic models for the API surface |
| `config_store.py` | `config.json`, atomic writes |
| `secret_store.py` | Fernet-encrypted token + integration secrets |
| `log_store.py` | Capped JSONL event log, filter/paginate/export |
| `ip_provider.py` | Public IP lookup |
| `cloudflare_client.py` | Cloudflare API wrapper with retryable errors |
| `sync_engine.py` | Sync cycle + retry + state file |
| `integration_engine.py` | Outbound webhooks with `{{template}}` rendering |
| `api.py` | Routes under `/api` |
| `main.py` | App + static mount |
| `cli.py` | `sync-once`, `verify-token`, `print-status` |

## Run

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
DNS_SYNCER_DEV=1 uvicorn app.main:app --reload --port 5055
pytest
```
