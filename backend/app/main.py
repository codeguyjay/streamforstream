from __future__ import annotations

import asyncio
import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes_streams, routes_twitch, routes_views
from app.storage import create_storage_from_env
from app.twitch.client import TwitchClient

load_dotenv()

log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(level=getattr(logging, log_level, logging.INFO))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="StreamBaton API",
    description="Backend API for the StreamBaton anonymous Twitch viewer exchange flow.",
    version="0.1.0",
)

def _frontend_origins() -> list[str]:
    raw_origins = os.environ.get("FRONTEND_ORIGINS", "")
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    if origins:
        return origins

    frontend_origin = os.environ.get("FRONTEND_ORIGIN", "http://localhost:3000").strip()
    if frontend_origin:
        return [frontend_origin]
    return ["http://localhost:3000"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=_frontend_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.state.streaming_store = create_storage_from_env()
app.state.twitch_client = TwitchClient(
    client_id=os.environ.get("TWITCH_CLIENT_ID", ""),
    client_secret=os.environ.get("TWITCH_CLIENT_SECRET", ""),
)


def _sweeper_interval_seconds(default: int = 300) -> int:
    raw = os.environ.get("TWITCH_SWEEPER_INTERVAL_SECONDS")
    if raw is None:
        return default
    try:
        return max(30, int(raw))
    except ValueError:
        return default


async def _sweeper_loop() -> None:
    interval_seconds = _sweeper_interval_seconds()
    while True:
        try:
            await routes_streams.run_live_sweeper_once(app.state.streaming_store, app.state.twitch_client)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Live stream sweeper failed.")
        await asyncio.sleep(interval_seconds)


@app.on_event("startup")
async def _start_background_tasks() -> None:
    app.state.live_sweeper_task = asyncio.create_task(_sweeper_loop())
    logger.info("Started live stream sweeper task.")


@app.on_event("shutdown")
async def _stop_background_tasks() -> None:
    task = getattr(app.state, "live_sweeper_task", None)
    if not task:
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
    logger.info("Stopped live stream sweeper task.")


app.include_router(routes_twitch.router, prefix="/api")
app.include_router(routes_streams.router, prefix="/api")
app.include_router(routes_views.router, prefix="/api")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "Welcome to StreamBaton API", "docs": "/docs", "version": "0.1.0"}


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "healthy"}
