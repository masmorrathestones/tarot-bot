from typing import Any

from pydantic import BaseModel, Field


class TestWhatsAppMessageRequest(BaseModel):
    from_number: str = Field(min_length=5, max_length=32)
    display_name: str | None = Field(default=None, max_length=120)
    text: str = Field(min_length=1, max_length=4000)


class TestWhatsAppMessageResponse(BaseModel):
    outgoing_messages: list[str | dict[str, Any]]
