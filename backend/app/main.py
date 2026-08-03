"""FastAPI app: mounts the API router and serves the static frontend."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app import VERSION, log_store, paths, scheduler
from app.api import router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    log_store.append("INFO", "SERVICE_STARTED", "Service started")
    scheduler.start()
    try:
        yield
    finally:
        scheduler.stop()


app = FastAPI(title="DNS Syncer", version=VERSION, lifespan=lifespan)
app.include_router(router)


@app.get("/")
def index():
    return FileResponse(paths.FRONTEND_DIR / "index.html",
                        headers={"Cache-Control": "no-cache"})


# Static assets. Mounted last so /api takes precedence.
for sub in ("styles", "js", "assets"):
    d = paths.FRONTEND_DIR / sub
    if d.is_dir():
        app.mount(f"/{sub}", StaticFiles(directory=str(d)), name=sub)
