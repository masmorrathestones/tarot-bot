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

MYSTIC_INTUITION_DESCRIPTIONS = {
    "Lawful Good": "Emphasize constructive outcomes through responsibility, commitments, cooperation, stable structures, protection, repair, and trustworthy support.",
    "Neutral Good": "Emphasize benevolent openings, healing, generosity, mutual benefit, emotional support, and practical opportunities without requiring a specific structure or path.",
    "Chaotic Good": "Emphasize liberating change, unexpected positive turns, courage to break stale patterns, unconventional opportunities, spontaneity, and growth through freedom.",
    "Lawful Neutral": "Emphasize rules, duties, institutions, routines, contracts, consequences, boundaries, order, and the value or cost of maintaining structure regardless of whether it feels pleasant.",
    "Chaotic Neutral": "Emphasize volatility, surprise, experimentation, rupture, unpredictability, freedom, unstable conditions, and the possibility that events escape established plans.",
    "Lawful Evil": "Emphasize risks arising through rigid systems, coercive commitments, hierarchy, manipulation through rules, controlling dynamics, burdensome obligations, or harmful consequences hidden inside apparently orderly arrangements.",
    "Neutral Evil": "Emphasize self-interest, temptation, loss, exploitation, resentment, hidden costs, emotional shadow, or situations where caution is needed because incentives may not be benevolent.",
    "Chaotic Evil": "Emphasize disruptive risk, impulsive conflict, destructive rupture, instability, betrayal of expectations, uncontrolled escalation, or situations where disorder can amplify an already difficult tendency.",
}

INTUITION_CHANCE_BASIS_POINTS = 800
INTUITION_ROLL_SCALE = 10_000
MAX_INTUITIONS = 2


@dataclass(frozen=True)
class MysticIntuition:
    alignment: str
    weight: int

    @property
    def description(self) -> str:
        return MYSTIC_INTUITION_DESCRIPTIONS[self.alignment]

    def to_dict(self) -> dict:
        return {"alignment": self.alignment, "weight": self.weight}

    @classmethod
    def from_dict(cls, data: dict) -> "MysticIntuition":
        alignment = str(data.get("alignment") or "")
        weight = int(data.get("weight") or 0)
        if alignment not in MYSTIC_INTUITION_TYPES:
            raise ValueError("Unknown mystic intuition alignment.")
        if not 1 <= weight <= 10:
            raise ValueError("Mystic intuition weight must be between 1 and 10.")
        return cls(alignment=alignment, weight=weight)


def _random_intuition(min_weight: int = 1) -> MysticIntuition:
    alignment = MYSTIC_INTUITION_TYPES[secrets.randbelow(len(MYSTIC_INTUITION_TYPES))]
    weight = secrets.randbelow(11 - min_weight) + min_weight
    return MysticIntuition(alignment=alignment, weight=weight)


def draw_mystic_intuitions() -> list[MysticIntuition]:
    result: list[MysticIntuition] = []
    for _ in range(MAX_INTUITIONS):
        if secrets.randbelow(INTUITION_ROLL_SCALE) >= INTUITION_CHANCE_BASIS_POINTS:
            continue
        result.append(_random_intuition())
    return result


def enforce_contextual_intuitions(
    intuitions: list[MysticIntuition],
    symbolic_signals: list[dict] | None,
) -> list[MysticIntuition]:
    """Apply deterministic minimum intuition rules after cards are known."""
    result = list(intuitions[:MAX_INTUITIONS])
    signals = symbolic_signals or []
    has_recurrence = any(
        signal.get("type") in {"last_four_recurrence", "weekly_recurrence"}
        for signal in signals
    )
    has_arcana_match = any(
        signal.get("type") in {"personal_arcana_match", "year_arcana_match"}
        for signal in signals
    )

    if has_arcana_match:
        while len(result) < 2:
            result.append(_random_intuition())
        if not any(item.weight > 5 for item in result):
            target = result[0]
            result[0] = MysticIntuition(target.alignment, secrets.randbelow(5) + 6)
        return result[:2]

    if has_recurrence:
        if not result:
            result.append(_random_intuition(min_weight=5))
        elif not any(item.weight >= 5 for item in result):
            target = result[0]
            result[0] = MysticIntuition(target.alignment, secrets.randbelow(6) + 5)

    return result[:MAX_INTUITIONS]
