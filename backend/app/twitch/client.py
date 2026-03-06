from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import httpx

from app.domain.streaming import ResolvedChannel, StreamState

logger = logging.getLogger(__name__)


class TwitchClient:
    token_url = "https://id.twitch.tv/oauth2/token"
    api_base_url = "https://api.twitch.tv/helix"

    def __init__(self, *, client_id: str, client_secret: str) -> None:
        self.client_id = client_id.strip()
        self.client_secret = client_secret.strip()
        self._app_token: str | None = None
        self._app_token_expires_at: datetime | None = None

    @property
    def configured(self) -> bool:
        return bool(self.client_id and self.client_secret)

    async def resolve_channel(self, channel_input: str) -> ResolvedChannel:
        login = channel_input.strip().lower().removeprefix("https://www.twitch.tv/").removeprefix("https://twitch.tv/").strip("/")
        if not login:
            raise ValueError("A Twitch channel is required.")

        response = await self._helix_get("/users", params={"login": login})
        items = response.get("data", [])
        if not items:
            raise LookupError(f"Twitch channel '{login}' was not found.")

        item = items[0]
        canonical_login = item["login"].strip().lower()
        return ResolvedChannel(
            channel_login=canonical_login,
            channel_display_name=item.get("display_name", canonical_login),
            profile_image_url=item.get("profile_image_url", ""),
            channel_url=f"https://www.twitch.tv/{canonical_login}",
        )

    async def get_live_stream(self, channel_login: str) -> StreamState:
        profile = await self.resolve_channel(channel_login)
        response = await self._helix_get("/streams", params={"user_login": profile.channel_login})
        items = response.get("data", [])
        if not items:
            return StreamState(
                channel_login=profile.channel_login,
                channel_display_name=profile.channel_display_name,
                profile_image_url=profile.profile_image_url,
                channel_url=profile.channel_url,
                stream_title="",
                game_name="",
                viewer_count=0,
                is_live=False,
            )

        item = items[0]
        return StreamState(
            channel_login=profile.channel_login,
            channel_display_name=profile.channel_display_name,
            profile_image_url=profile.profile_image_url,
            channel_url=profile.channel_url,
            stream_title=item.get("title", ""),
            game_name=item.get("game_name", ""),
            viewer_count=int(item.get("viewer_count", 0)),
            is_live=True,
        )

    async def _helix_get(self, path: str, *, params: dict[str, str]) -> dict:
        if not self.configured:
            raise RuntimeError("TWITCH_CLIENT_ID and TWITCH_CLIENT_SECRET must be configured.")

        headers = await self._headers()
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(f"{self.api_base_url}{path}", headers=headers, params=params)
            response.raise_for_status()
            return response.json()

    async def _headers(self) -> dict[str, str]:
        token = await self._app_access_token()
        return {
            "Authorization": f"Bearer {token}",
            "Client-Id": self.client_id,
        }

    async def _app_access_token(self) -> str:
        now = datetime.now(timezone.utc)
        if self._app_token and self._app_token_expires_at and now < self._app_token_expires_at:
            return self._app_token

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                self.token_url,
                params={
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                    "grant_type": "client_credentials",
                },
            )
            response.raise_for_status()
            payload = response.json()

        access_token = payload["access_token"]
        expires_in = int(payload.get("expires_in", 3600))
        self._app_token = access_token
        self._app_token_expires_at = now + timedelta(seconds=max(60, expires_in - 60))
        logger.info("Fetched Twitch app access token.")
        return access_token
