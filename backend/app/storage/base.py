from __future__ import annotations

from typing import Protocol

from app.domain.streaming import (
    LiveStreamRecord,
    PaginatedLiveStreamResult,
    PointState,
    ResolvedChannel,
    SortMode,
    StreamState,
    ViewCreditResult,
    ViewerType,
)


class StreamingStore(Protocol):
    def upsert_profile(self, channel: ResolvedChannel) -> ResolvedChannel: ...

    def get_profile(self, channel_login: str) -> ResolvedChannel | None: ...

    def get_point_state(self, channel_login: str) -> PointState: ...

    def upsert_live_stream(self, profile: ResolvedChannel, stream_state: StreamState) -> LiveStreamRecord: ...

    def get_live_stream(self, channel_login: str) -> LiveStreamRecord | None: ...

    def remove_live_stream(self, channel_login: str) -> bool: ...

    def list_live_streams(
        self,
        *,
        exclude_channel_login: str | None = None,
        limit: int = 20,
        cursor: dict[str, str] | None = None,
        sort_mode: SortMode,
    ) -> PaginatedLiveStreamResult: ...

    def all_live_logins(self) -> list[str]: ...

    def refresh_live_stream(self, channel_login: str, stream_state: StreamState) -> LiveStreamRecord | None: ...

    def apply_view_report(
        self,
        *,
        viewer_id: str,
        viewer_type: ViewerType,
        earning_channel_login: str,
        viewed_channel_login: str,
        viewed_minute: str,
    ) -> ViewCreditResult: ...
