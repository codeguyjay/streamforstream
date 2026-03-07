from typing import Annotated

from pydantic import BaseModel, StringConstraints


ChannelLogin = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=255)]
ViewedMinute = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]


class ReportViewRequest(BaseModel):
    earning_channel_login: ChannelLogin
    viewed_channel_login: ChannelLogin
    viewed_minute: ViewedMinute


class ReportViewResponse(BaseModel):
    credited: bool
    viewer_total_points: int
