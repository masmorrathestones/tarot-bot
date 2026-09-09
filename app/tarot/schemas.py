from typing import Optional
from pydantic import BaseModel, Field

from app.tarot.enums import ArcanaType, Suit, Orientation


class DrawRequest(BaseModel):
    spread_code: str = Field(default="THREE_CARD_SITUATION")
    allow_reversed: bool = True
    question: Optional[str] = Field(default=None, max_length=500)
    context: Optional[str] = Field(default=None, max_length=1000)


class SpreadPositionResponse(BaseModel):
    index: int
    code: str
    name: str
    description: str


class SpreadResponse(BaseModel):
    code: str
    name: str
    description: str
    positions: list[SpreadPositionResponse]


class CardMetadataResponse(BaseModel):
    upright_keywords: list[str]
    upright_meaning: str
    reversed_keywords: list[str]
    reversed_meaning: str
    element: Optional[str] = None
    astrological_association: str
    source_page: int
    reversed_is_derived: bool


class TarotCardResponse(BaseModel):
    id: int
    code: str
    name: str
    arcana: ArcanaType
    number: Optional[int] = None
    suit: Optional[Suit] = None
    metadata: Optional[CardMetadataResponse] = None


class DrawnCardResponse(BaseModel):
    position: SpreadPositionResponse
    orientation: Orientation
    card: TarotCardResponse


class DrawResponse(BaseModel):
    deck: str
    spread: SpreadResponse
    question: Optional[str] = None
    context: Optional[str] = None
    cards: list[DrawnCardResponse]


class InterpretationKnowledgeResponse(BaseModel):
    card_code: str
    card_name: str
    general: str
    career: str
    consciousness: str
    relationships: str
    source_page: int
    source: str
    language: str
    is_paraphrase: bool


class UserProfileContextRequest(BaseModel):
    sun_sign: Optional[str] = Field(default=None, max_length=30)
    moon_sign: Optional[str] = Field(default=None, max_length=30)
    rising_sign: Optional[str] = Field(default=None, max_length=30)
    mbti: Optional[str] = Field(default=None, max_length=10)


class TarotReadRequest(BaseModel):
    user_id: int = Field(gt=0)
    spread_code: str = Field(default="THREE_CARD_SITUATION")
    allow_reversed: bool = True
    question: str = Field(min_length=3, max_length=500)
    context: Optional[str] = Field(default=None, max_length=1000)


class TarotInterpretationResponse(BaseModel):
    narrative: str
    card_analysis: str
    synthesis: str


class TarotReadResponse(BaseModel):
    reading_id: int
    status: str
    retry_count: int
    user_id: int
    deck: str
    spread: SpreadResponse
    question: str
    context: Optional[str] = None
    profile_snapshot: dict
    cards: list[DrawnCardResponse]
    interpretation: TarotInterpretationResponse


class PersistedReadingResponse(BaseModel):
    reading_id: int
    status: str
    retry_count: int
    user_id: int
    deck: str
    spread_code: str
    question: str
    context: Optional[str] = None
    profile_snapshot: dict
    cards: list[DrawnCardResponse]
    interpretation: Optional[TarotInterpretationResponse] = None
    error_message: Optional[str] = None
