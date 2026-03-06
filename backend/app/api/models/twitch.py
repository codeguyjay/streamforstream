from pydantic import BaseModel, Field


class ResolveChannelRequest(BaseModel):
    channel_input: str = Field(min_length=1, max_length=255)


class ResolveChannelResponse(BaseModel):
    channel_login: str
    channel_display_name: str
    profile_image_url: str
    channel_url: str
