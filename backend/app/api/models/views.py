from pydantic import BaseModel, Field


class ReportViewRequest(BaseModel):
    viewer_channel_login: str = Field(min_length=1, max_length=255)
    target_channel_login: str = Field(min_length=1, max_length=255)
    viewed_minute: str = Field(min_length=1, max_length=64)


class ReportViewResponse(BaseModel):
    credited: bool
    viewer_points_balance: int
