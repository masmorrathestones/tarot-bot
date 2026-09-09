from enum import Enum


class ArcanaType(str, Enum):
    MAJOR = "MAJOR"
    MINOR = "MINOR"


class Suit(str, Enum):
    WANDS = "WANDS"
    CUPS = "CUPS"
    SWORDS = "SWORDS"
    PENTACLES = "PENTACLES"


class Orientation(str, Enum):
    UPRIGHT = "UPRIGHT"
    REVERSED = "REVERSED"
