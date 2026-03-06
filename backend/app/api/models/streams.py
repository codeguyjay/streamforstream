from datetime import datetime

from pydantic import BaseModel, Field


class GoLiveRequest(BaseModel):
    channel_login: str = Field(min_length=1, max_length=255)


class GoOfflineRequest(BaseModel):
    channel_login: str = Field(min_length=1, max_length=255)


class LiveStreamerResponse(BaseModel):
    channel_login: str
    channel_display_name: str
    profile_image_url: str
    channel_url: str
    is_live: bool
    stream_title: str
    game_name: str
    viewer_count: int
    went_live_at: datetime
    points_balance: int


class LiveStreamersResponse(BaseModel):
    items: list[LiveStreamerResponse]
    checked_at: datetime
    viewer_points_balance: int
    viewer_is_live: bool


class SuccessResponse(BaseModel):
    success: bool
