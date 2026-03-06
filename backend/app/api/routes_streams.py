from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_streaming_store, get_twitch_client
from app.api.pagination import decode_pagination_cursor, encode_pagination_cursor
from app.api.models.streams import GoLiveRequest, GoOfflineRequest, LiveStreamersResponse, LiveStreamerResponse, SuccessResponse
from app.domain.streaming import VIEWER_COUNT_DESC, LiveStreamRecord, SortMode
from app.storage import StreamingStore
from app.twitch.client import TwitchClient
from app.twitch.service import sweep_live_streams

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/streams", tags=["streams"])


def _cursor_scope(*, sort_mode: SortMode, exclude_channel_login: str | None) -> dict[str, str]:
    return {
        "route": "streams_live",
        "sort_mode": sort_mode,
        "exclude_channel_login": (exclude_channel_login or "").strip().lower(),
    }


def _to_response(record: LiveStreamRecord) -> LiveStreamerResponse:
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
        total_points=record.total_points,
    )


@router.get("/live", response_model=LiveStreamersResponse)
async def get_live_streamers(
    exclude_channel_login: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    sort_mode: Literal["viewer_count_desc", "engagement_priority"] = Query(default=VIEWER_COUNT_DESC),
    cursor: str | None = Query(default=None),
    store: StreamingStore = Depends(get_streaming_store),
) -> LiveStreamersResponse:
    logger.info("GET /streams/live exclude=%s limit=%s sort_mode=%s", exclude_channel_login, limit, sort_mode)
    start_key = decode_pagination_cursor(
        cursor,
        expected_scope=_cursor_scope(sort_mode=sort_mode, exclude_channel_login=exclude_channel_login),
    )
    try:
        page = store.list_live_streams(
            exclude_channel_login=exclude_channel_login,
            limit=limit,
            cursor=start_key,
            sort_mode=sort_mode,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    next_cursor = (
        encode_pagination_cursor(
            token=page.next_cursor,
            scope=_cursor_scope(sort_mode=sort_mode, exclude_channel_login=exclude_channel_login),
        )
        if page.next_cursor
        else None
    )
    return LiveStreamersResponse(
        items=[_to_response(record) for record in page.items],
        checked_at=datetime.now(timezone.utc),
        viewer_total_points=store.get_point_state(exclude_channel_login).total_points if exclude_channel_login else 0,
        viewer_is_live=bool(exclude_channel_login and store.get_live_stream(exclude_channel_login)),
        next_cursor=next_cursor,
        has_more=next_cursor is not None,
    )


@router.post("/go-live", response_model=LiveStreamerResponse)
async def go_live(
    request: GoLiveRequest,
    store: StreamingStore = Depends(get_streaming_store),
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
    return _to_response(record)


@router.post("/go-offline", response_model=SuccessResponse)
async def go_offline(
    request: GoOfflineRequest,
    store: StreamingStore = Depends(get_streaming_store),
) -> SuccessResponse:
    logger.info("POST /streams/go-offline channel=%s", request.channel_login)
    removed = store.remove_live_stream(request.channel_login)
    return SuccessResponse(success=removed)


async def run_live_sweeper_once(store: StreamingStore, twitch_client: TwitchClient) -> None:
    await sweep_live_streams(store, twitch_client)
