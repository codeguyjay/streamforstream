from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_streaming_store, get_twitch_client
from app.api.models.twitch import ResolveChannelRequest, ResolveChannelResponse
from app.storage import StreamingStore
from app.twitch.client import TwitchClient

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/twitch", tags=["twitch"])


@router.post("/resolve-channel", response_model=ResolveChannelResponse)
async def resolve_channel(
    request: ResolveChannelRequest,
    store: StreamingStore = Depends(get_streaming_store),
    twitch_client: TwitchClient = Depends(get_twitch_client),
) -> ResolveChannelResponse:
    logger.info("POST /twitch/resolve-channel input=%s", request.channel_input)
    try:
        channel = await twitch_client.resolve_channel(request.channel_input)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    store.upsert_profile(channel)
    return ResolveChannelResponse(
        channel_login=channel.channel_login,
        channel_display_name=channel.channel_display_name,
        profile_image_url=channel.profile_image_url,
        channel_url=channel.channel_url,
    )
