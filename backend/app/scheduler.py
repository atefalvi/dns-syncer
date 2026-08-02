"""In-process safety-net scheduler for automatic syncs.

The systemd timer remains the primary scheduler. This background checker uses
the same due logic and lock as the timer path so a broken timer cannot leave DNS
records stale while the web service is still running.
"""
import os
import threading

from app import log_store, sync_engine

CHECK_SECONDS = 60
INITIAL_DELAY_SECONDS = 15

_stop = threading.Event()
_thread: threading.Thread | None = None


def _disabled() -> bool:
    return bool(os.environ.get("DNS_SYNCER_DISABLE_SCHEDULER")
                or os.environ.get("DNS_SYNCER_DEV"))


def _loop() -> None:
    if _stop.wait(INITIAL_DELAY_SECONDS):
        return
    while not _stop.is_set():
        try:
            sync_engine.run_sync_if_due(source="app-scheduler")
        except Exception as e:
            log_store.append("ERROR", "SCHEDULER_FAILED",
                             f"Automatic sync check failed: {e}")
        _stop.wait(CHECK_SECONDS)


def start() -> None:
    global _thread
    if _disabled() or (_thread and _thread.is_alive()):
        return
    _stop.clear()
    _thread = threading.Thread(target=_loop, name="dns-syncer-scheduler",
                               daemon=True)
    _thread.start()
    log_store.append("INFO", "SCHEDULER_STARTED",
                     "Automatic sync scheduler started")


def stop() -> None:
    _stop.set()
