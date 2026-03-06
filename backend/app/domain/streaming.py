from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal


SortMode = Literal["viewer_count_desc", "engagement_priority"]

VIEWER_COUNT_DESC: SortMode = "viewer_count_desc"
ENGAGEMENT_PRIORITY: SortMode = "engagement_priority"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(slots=True)
class ResolvedChannel:
    channel_login: str
    channel_display_name: str
    profile_image_url: str
    channel_url: str


@dataclass(slots=True)
class StreamState:
    channel_login: str
    channel_display_name: str
    profile_image_url: str
    channel_url: str
    stream_title: str
    game_name: str
    viewer_count: int
    is_live: bool


@dataclass(slots=True)
class LiveStreamRecord:
    channel_login: str
    channel_display_name: str
    profile_image_url: str
    channel_url: str
    stream_title: str
    game_name: str
    viewer_count: int
    is_live: bool
    went_live_at: datetime
    updated_at: datetime
    point_balance: int
    total_points: int


@dataclass(slots=True)
class PointState:
    point_balance: int
    total_points: int


@dataclass(slots=True)
class PaginatedLiveStreamResult:
    items: list[LiveStreamRecord]
    next_cursor: dict[str, str] | None = None


@dataclass(slots=True)
class ViewCreditResult:
    credited: bool
    viewer_points_balance: int
    viewer_total_points: int
