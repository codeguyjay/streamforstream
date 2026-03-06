from __future__ import annotations

import logging

from app.storage import StreamingStore
from app.twitch.client import TwitchClient

logger = logging.getLogger(__name__)


async def sweep_live_streams(store: StreamingStore, twitch_client: TwitchClient) -> None:
    for channel_login in store.all_live_logins():
        stream_state = await twitch_client.get_live_stream(channel_login)
        if not stream_state.is_live:
            store.remove_live_stream(channel_login)
            logger.info("Removed offline channel from live list: %s", channel_login)
            continue

        store.refresh_live_stream(channel_login, stream_state)
