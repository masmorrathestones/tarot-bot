import secrets
from dataclasses import dataclass


MYSTIC_INTUITION_TYPES = (
    "Lawful Good",
    "Neutral Good",
    "Chaotic Good",
    "Lawful Neutral",
    "Chaotic Neutral",
    "Lawful Evil",
    "Neutral Evil",
    "Chaotic Evil",
)

# Each of the two independent intuition slots has a 1.2% chance to activate.
# Most readings therefore receive no intuition at all.
INTUITION_CHANCE_BASIS_POINTS = 360
INTUITION_ROLL_SCALE = 10_000
MAX_INTUITIONS = 2


@dataclass(frozen=True)
class MysticIntuition:
    alignment: str
    weight: int

    def to_dict(self) -> dict:
        return {
            "alignment": self.alignment,
            "weight": self.weight,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MysticIntuition":
        alignment = str(data.get("alignment") or "")
        weight = int(data.get("weight") or 0)
        if alignment not in MYSTIC_INTUITION_TYPES:
            raise ValueError("Unknown mystic intuition alignment.")
        if not 1 <= weight <= 10:
            raise ValueError("Mystic intuition weight must be between 1 and 10.")
        return cls(alignment=alignment, weight=weight)


def draw_mystic_intuitions() -> list[MysticIntuition]:
    """Draw zero, one, or two hidden intuition modifiers for a reading."""
    result: list[MysticIntuition] = []

    for _ in range(MAX_INTUITIONS):
        if secrets.randbelow(INTUITION_ROLL_SCALE) >= INTUITION_CHANCE_BASIS_POINTS:
            continue

        alignment = MYSTIC_INTUITION_TYPES[
            secrets.randbelow(len(MYSTIC_INTUITION_TYPES))
        ]
        weight = secrets.randbelow(10) + 1
        result.append(MysticIntuition(alignment=alignment, weight=weight))

    return result
