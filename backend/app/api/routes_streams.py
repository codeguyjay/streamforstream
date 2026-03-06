from __future__ import annotations

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_streaming_store, get_twitch_client
from app.api.models.streams import GoLiveRequest, GoOfflineRequest, LiveStreamersResponse, LiveStreamerResponse, SuccessResponse
from app.storage import InMemoryStreamingStore
from app.twitch.client import TwitchClient
from app.twitch.service import sweep_live_streams

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/streams", tags=["streams"])


def _to_response(store: InMemoryStreamingStore, channel_login: str) -> LiveStreamerResponse:
    record = store.get_live_stream(channel_login)
    if not record:
        raise HTTPException(status_code=404, detail=f"Live stream '{channel_login}' was not found.")

    return LiveStreamerResponse(
        channel_login=record.channel_login,
        channel_display_name=record.channel_display_name,
        profile_image_url=record.profile_image_url,
        channel_url=record.channel_url,
        is_live=record.is_live,
        stream_title=record.stream_title,
        game_name=record.game_name,
        viewer_count=record.viewer_count,
        went_live_at=record.went_live_at,
        points_balance=store.points_for(record.channel_login),
    )


@router.get("/live", response_model=LiveStreamersResponse)
async def get_live_streamers(
    exclude_channel_login: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    store: InMemoryStreamingStore = Depends(get_streaming_store),
) -> LiveStreamersResponse:
    logger.info("GET /streams/live exclude=%s limit=%s", exclude_channel_login, limit)
    items = [
        LiveStreamerResponse(
            channel_login=record.channel_login,
            channel_display_name=record.channel_display_name,
            profile_image_url=record.profile_image_url,
            channel_url=record.channel_url,
            is_live=record.is_live,
            stream_title=record.stream_title,
            game_name=record.game_name,
            viewer_count=record.viewer_count,
            went_live_at=record.went_live_at,
            points_balance=store.points_for(record.channel_login),
        )
        for record in store.list_live_streams(exclude_channel_login=exclude_channel_login, limit=limit)
    ]
    return LiveStreamersResponse(
        items=items,
        checked_at=datetime.now(timezone.utc),
        viewer_points_balance=store.points_for(exclude_channel_login or ""),
        viewer_is_live=bool(exclude_channel_login and store.get_live_stream(exclude_channel_login)),
    )


@router.post("/go-live", response_model=LiveStreamerResponse)
async def go_live(
    request: GoLiveRequest,
    store: InMemoryStreamingStore = Depends(get_streaming_store),
    twitch_client: TwitchClient = Depends(get_twitch_client),
) -> LiveStreamerResponse:
    logger.info("POST /streams/go-live channel=%s", request.channel_login)
    try:
        profile = await twitch_client.resolve_channel(request.channel_login)
        stream_state = await twitch_client.get_live_stream(profile.channel_login)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    if not stream_state.is_live:
        raise HTTPException(status_code=409, detail="This Twitch channel is not currently live.")

    store.upsert_profile(profile)
    record = store.upsert_live_stream(profile, stream_state)
    return LiveStreamerResponse(
        channel_login=record.channel_login,
        channel_display_name=record.channel_display_name,
        profile_image_url=record.profile_image_url,
        channel_url=record.channel_url,
        is_live=record.is_live,
        stream_title=record.stream_title,
        game_name=record.game_name,
        viewer_count=record.viewer_count,
        went_live_at=record.went_live_at,
        points_balance=store.points_for(record.channel_login),
    )


@router.post("/go-offline", response_model=SuccessResponse)
async def go_offline(
    request: GoOfflineRequest,
    store: InMemoryStreamingStore = Depends(get_streaming_store),
) -> SuccessResponse:
    logger.info("POST /streams/go-offline channel=%s", request.channel_login)
    removed = store.remove_live_stream(request.channel_login)
    return SuccessResponse(success=removed)


async def run_live_sweeper_once(store: InMemoryStreamingStore, twitch_client: TwitchClient) -> None:
    await sweep_live_streams(store, twitch_client)
