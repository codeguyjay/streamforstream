from pydantic import BaseModel, Field


class ReportViewRequest(BaseModel):
    earning_channel_login: str = Field(min_length=1, max_length=255)
    viewed_channel_login: str = Field(min_length=1, max_length=255)
    viewed_minute: str = Field(min_length=1, max_length=64)


class ReportViewResponse(BaseModel):
    credited: bool
    viewer_total_points: int
