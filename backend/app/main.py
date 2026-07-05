"""FastAPI app: mounts the API router and serves the static frontend."""
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import VERSION, log_store, paths
from app.api import router

app = FastAPI(title="DNS Syncer", version=VERSION)
app.include_router(router)


@app.on_event("startup")
def _on_startup():
    log_store.append("INFO", "SERVICE_STARTED", "Service started")


@app.get("/")
def index():
    return FileResponse(paths.FRONTEND_DIR / "index.html")


# Static assets. Mounted last so /api takes precedence.
for sub in ("styles", "js", "assets"):
    d = paths.FRONTEND_DIR / sub
    if d.is_dir():
        app.mount(f"/{sub}", StaticFiles(directory=str(d)), name=sub)
