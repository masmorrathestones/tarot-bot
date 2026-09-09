from dataclasses import dataclass
from typing import Optional

from app.tarot.enums import ArcanaType, Suit, Orientation
from app.tarot.metadata import CardMetadata


@dataclass(frozen=True)
class TarotCard:
    id: int
    code: str
    name: str
    arcana: ArcanaType
    number: Optional[int] = None
    suit: Optional[Suit] = None
    metadata: Optional[CardMetadata] = None


@dataclass(frozen=True)
class SpreadPosition:
    index: int
    code: str
    name: str
    description: str


@dataclass(frozen=True)
class Spread:
    code: str
    name: str
    description: str
    positions: tuple[SpreadPosition, ...]
    interpretation_instructions: str | None = None


@dataclass(frozen=True)
class DrawnCard:
    position: SpreadPosition
    card: TarotCard
    orientation: Orientation
