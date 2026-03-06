from __future__ import annotations

from dataclasses import replace
from datetime import datetime

from app.domain.streaming import LiveStreamRecord, ResolvedChannel, StreamState, ViewCreditResult, utc_now


class InMemoryStreamingStore:
    def __init__(self) -> None:
        self._profiles: dict[str, ResolvedChannel] = {}
        self._live_streams: dict[str, LiveStreamRecord] = {}
        self._points: dict[str, int] = {}
        self._credited_minutes: set[tuple[str, str, str]] = set()

    def upsert_profile(self, channel: ResolvedChannel) -> ResolvedChannel:
        self._profiles[channel.channel_login] = channel
        self._points.setdefault(channel.channel_login, 0)
        return channel

    def get_profile(self, channel_login: str) -> ResolvedChannel | None:
        return self._profiles.get(channel_login.strip().lower())

    def points_for(self, channel_login: str) -> int:
        return self._points.get(channel_login.strip().lower(), 0)

    def upsert_live_stream(self, profile: ResolvedChannel, stream_state: StreamState) -> LiveStreamRecord:
        login = profile.channel_login
        existing = self._live_streams.get(login)
        now = utc_now()
        went_live_at = existing.went_live_at if existing else now
        record = LiveStreamRecord(
            channel_login=login,
            channel_display_name=profile.channel_display_name,
            profile_image_url=profile.profile_image_url,
            channel_url=profile.channel_url,
            stream_title=stream_state.stream_title,
            game_name=stream_state.game_name,
            viewer_count=stream_state.viewer_count,
            is_live=stream_state.is_live,
            went_live_at=went_live_at,
            updated_at=now,
        )
        self._profiles[login] = profile
        self._points.setdefault(login, 0)
        self._live_streams[login] = record
        return record

    def get_live_stream(self, channel_login: str) -> LiveStreamRecord | None:
        return self._live_streams.get(channel_login.strip().lower())

    def remove_live_stream(self, channel_login: str) -> bool:
        return self._live_streams.pop(channel_login.strip().lower(), None) is not None

    def list_live_streams(self, *, exclude_channel_login: str | None = None, limit: int = 20) -> list[LiveStreamRecord]:
        exclude = exclude_channel_login.strip().lower() if exclude_channel_login else None
        items = [record for login, record in self._live_streams.items() if login != exclude]
        items.sort(key=lambda item: (-item.viewer_count, item.went_live_at))
        return items[:limit]

    def all_live_logins(self) -> list[str]:
        return list(self._live_streams.keys())

    def refresh_live_stream(self, channel_login: str, stream_state: StreamState) -> LiveStreamRecord | None:
        existing = self._live_streams.get(channel_login.strip().lower())
        if not existing:
            return None
        refreshed = replace(
            existing,
            stream_title=stream_state.stream_title,
            game_name=stream_state.game_name,
            viewer_count=stream_state.viewer_count,
            is_live=stream_state.is_live,
            updated_at=utc_now(),
        )
        self._live_streams[channel_login.strip().lower()] = refreshed
        return refreshed

    def credit_view_minute(self, *, viewer_channel_login: str, target_channel_login: str, viewed_minute: str) -> ViewCreditResult:
        viewer_login = viewer_channel_login.strip().lower()
        target_login = target_channel_login.strip().lower()
        if viewer_login == target_login:
            raise ValueError("A streamer cannot earn points by viewing their own channel.")

        key = (viewer_login, target_login, viewed_minute)
        self._points.setdefault(viewer_login, 0)
        self._points.setdefault(target_login, 0)

        if key in self._credited_minutes:
            return ViewCreditResult(credited=False, viewer_points_balance=self._points[viewer_login])

        self._credited_minutes.add(key)
        self._points[viewer_login] += 1
        return ViewCreditResult(credited=True, viewer_points_balance=self._points[viewer_login])


def create_in_memory_storage() -> InMemoryStreamingStore:
    return InMemoryStreamingStore()
