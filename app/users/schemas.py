from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class UserProfileInput(BaseModel):
    sun_sign: Optional[str] = Field(default=None, max_length=30)
    moon_sign: Optional[str] = Field(default=None, max_length=30)
    rising_sign: Optional[str] = Field(default=None, max_length=30)
    mbti: Optional[str] = Field(default=None, max_length=10)


class CreateUserRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    whatsapp_number: str = Field(min_length=5, max_length=32)
    profile: Optional[UserProfileInput] = None


class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    whatsapp_number: Optional[str] = Field(
        default=None, min_length=5, max_length=32
    )
    profile: Optional[UserProfileInput] = None


class UserProfileResponse(BaseModel):
    sun_sign: Optional[str] = None
    moon_sign: Optional[str] = None
    rising_sign: Optional[str] = None
    mbti: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    name: str
    whatsapp_number: str
    profile: UserProfileResponse
    created_at: datetime
    updated_at: datetime
