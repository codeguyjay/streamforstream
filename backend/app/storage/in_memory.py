from __future__ import annotations

from dataclasses import replace

from app.domain.streaming import (
    ENGAGEMENT_PRIORITY,
    VIEWER_COUNT_DESC,
    LiveStreamRecord,
    PaginatedLiveStreamResult,
    PointState,
    ResolvedChannel,
    SortMode,
    StreamState,
    ViewCreditResult,
    utc_now,
)


def _normalize_channel_login(channel_login: str) -> str:
    return channel_login.strip().lower()


class InMemoryStreamingStore:
    def __init__(self) -> None:
        self._profiles: dict[str, ResolvedChannel] = {}
        self._live_streams: dict[str, LiveStreamRecord] = {}
        self._point_state: dict[str, PointState] = {}
        self._credited_minutes: set[tuple[str, str]] = set()

    def _ensure_point_state(self, channel_login: str) -> PointState:
        login = _normalize_channel_login(channel_login)
        state = self._point_state.get(login)
        if state is None:
            state = PointState(point_balance=0, total_points=0)
            self._point_state[login] = state
        return state

    def _set_point_state(self, channel_login: str, state: PointState) -> None:
        login = _normalize_channel_login(channel_login)
        self._point_state[login] = state
        if login in self._live_streams:
            self._live_streams[login] = replace(
                self._live_streams[login],
                point_balance=state.point_balance,
                total_points=state.total_points,
            )

    def upsert_profile(self, channel: ResolvedChannel) -> ResolvedChannel:
        login = _normalize_channel_login(channel.channel_login)
        self._profiles[login] = replace(channel, channel_login=login)
        self._ensure_point_state(login)
        return self._profiles[login]

    def get_profile(self, channel_login: str) -> ResolvedChannel | None:
        return self._profiles.get(_normalize_channel_login(channel_login))

    def get_point_state(self, channel_login: str) -> PointState:
        return self._ensure_point_state(channel_login)

    def upsert_live_stream(self, profile: ResolvedChannel, stream_state: StreamState) -> LiveStreamRecord:
        login = _normalize_channel_login(profile.channel_login)
        existing = self._live_streams.get(login)
        points = self._ensure_point_state(login)
        now = utc_now()
        record = LiveStreamRecord(
            channel_login=login,
            channel_display_name=profile.channel_display_name,
            profile_image_url=profile.profile_image_url,
            channel_url=profile.channel_url,
            stream_title=stream_state.stream_title,
            game_name=stream_state.game_name,
            viewer_count=stream_state.viewer_count,
            is_live=stream_state.is_live,
            went_live_at=existing.went_live_at if existing else now,
            updated_at=now,
            point_balance=points.point_balance,
            total_points=points.total_points,
        )
        self._profiles[login] = replace(profile, channel_login=login)
        self._live_streams[login] = record
        return record

    def get_live_stream(self, channel_login: str) -> LiveStreamRecord | None:
        return self._live_streams.get(_normalize_channel_login(channel_login))

    def remove_live_stream(self, channel_login: str) -> bool:
        return self._live_streams.pop(_normalize_channel_login(channel_login), None) is not None

    def list_live_streams(
        self,
        *,
        exclude_channel_login: str | None = None,
        limit: int = 20,
        cursor: dict[str, str] | None = None,
        sort_mode: SortMode,
    ) -> PaginatedLiveStreamResult:
        exclude = _normalize_channel_login(exclude_channel_login) if exclude_channel_login else None
        items = [record for login, record in self._live_streams.items() if login != exclude]
        if sort_mode == ENGAGEMENT_PRIORITY:
            items.sort(key=lambda item: (item.viewer_count, -item.point_balance, item.went_live_at, item.channel_login))
        elif sort_mode == VIEWER_COUNT_DESC:
            items.sort(key=lambda item: (-item.viewer_count, item.went_live_at, item.channel_login))
        else:
            raise ValueError("Unsupported sort mode")

        offset = 0
        if cursor:
            raw_offset = cursor.get("offset")
            if raw_offset is None:
                raise ValueError("Invalid cursor payload")
            try:
                offset = max(0, int(raw_offset))
            except ValueError as exc:
                raise ValueError("Invalid cursor payload") from exc

        page = items[offset : offset + limit]
        next_offset = offset + len(page)
        next_cursor = {"offset": str(next_offset)} if next_offset < len(items) else None
        return PaginatedLiveStreamResult(items=page, next_cursor=next_cursor)

    def all_live_logins(self) -> list[str]:
        return list(self._live_streams.keys())

    def refresh_live_stream(self, channel_login: str, stream_state: StreamState) -> LiveStreamRecord | None:
        login = _normalize_channel_login(channel_login)
        existing = self._live_streams.get(login)
        if not existing:
            return None
        points = self._ensure_point_state(login)
        refreshed = replace(
            existing,
            stream_title=stream_state.stream_title,
            game_name=stream_state.game_name,
            viewer_count=stream_state.viewer_count,
            is_live=stream_state.is_live,
            updated_at=utc_now(),
            point_balance=points.point_balance,
            total_points=points.total_points,
        )
        self._live_streams[login] = refreshed
        return refreshed

    def apply_view_report(
        self,
        *,
        viewer_channel_login: str,
        target_channel_login: str,
        viewed_minute: str,
    ) -> ViewCreditResult:
        viewer_login = _normalize_channel_login(viewer_channel_login)
        target_login = _normalize_channel_login(target_channel_login)
        if viewer_login == target_login:
            raise ValueError("A streamer cannot earn points by viewing their own channel.")

        key = (viewer_login, viewed_minute)
        viewer_state = self._ensure_point_state(viewer_login)
        target_state = self._ensure_point_state(target_login)

        if key in self._credited_minutes:
            return ViewCreditResult(
                credited=False,
                viewer_points_balance=viewer_state.point_balance,
                viewer_total_points=viewer_state.total_points,
            )

        self._credited_minutes.add(key)

        next_viewer_state = PointState(
            point_balance=viewer_state.point_balance + 1,
            total_points=viewer_state.total_points + 1,
        )
        next_target_state = PointState(
            point_balance=max(0, target_state.point_balance - 1),
            total_points=target_state.total_points,
        )
        self._set_point_state(viewer_login, next_viewer_state)
        self._set_point_state(target_login, next_target_state)

        return ViewCreditResult(
            credited=True,
            viewer_points_balance=next_viewer_state.point_balance,
            viewer_total_points=next_viewer_state.total_points,
        )


def create_in_memory_storage() -> InMemoryStreamingStore:
    return InMemoryStreamingStore()
