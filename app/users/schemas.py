from datetime import date, datetime, time
from typing import Any, Optional
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
    birth_date: Optional[date] = None
    birth_time: Optional[time] = None
    birth_place: Optional[str] = None
    birth_latitude: Optional[float] = None
    birth_longitude: Optional[float] = None
    birth_timezone: Optional[str] = None
    natal_chart: Optional[dict[str, Any]] = None
    zodiac_sign: Optional[str] = None
    personal_number: Optional[int] = None
    personal_arcana_number: Optional[int] = None
    personal_arcana_name: Optional[str] = None
    year_arcana_number: Optional[int] = None
    year_arcana_name: Optional[str] = None
    year_arcana_reference_year: Optional[int] = None


class UserResponse(BaseModel):
    id: int
    name: str
    whatsapp_number: str
    profile: UserProfileResponse
    created_at: datetime
    updated_at: datetime
