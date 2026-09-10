from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ScheduleXPostRequest(BaseModel):
    text: str = Field(min_length=1, max_length=25000)
    scheduled_at: datetime
    language: str | None = Field(default=None, max_length=5)
    media_path: str | None = Field(default=None, max_length=500)
    parent_source_key: str | None = Field(default=None, max_length=160)
    source_key: str | None = Field(default=None, max_length=160)


class ScheduledXPostResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    language: str | None
    source_key: str | None
    media_path: str | None
    parent_source_key: str | None
    scheduled_at: datetime
    status: str
    x_post_id: str | None
    error_message: str | None
    last_attempt_at: datetime | None
    sent_at: datetime | None
    created_at: datetime
    updated_at: datetime
