from __future__ import annotations

from fastapi import Request

from app.storage import InMemoryStreamingStore
from app.twitch.client import TwitchClient


def get_streaming_store(request: Request) -> InMemoryStreamingStore:
    return request.app.state.streaming_store


def get_twitch_client(request: Request) -> TwitchClient:
    return request.app.state.twitch_client
