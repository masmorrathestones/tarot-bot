import secrets
from dataclasses import dataclass

from app.tarot.enums import Orientation
from app.tarot.models import DrawnCard, SpreadPosition, TarotCard
from app.tarot.service import tarot_draw_service


@dataclass(frozen=True)
class FallenCandidate:
    card_code: str
    orientation: Orientation

    def to_dict(self) -> dict:
        return {
            "card_code": self.card_code,
            "orientation": self.orientation.value,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FallenCandidate":
        return cls(
            card_code=str(data["card_code"]),
            orientation=Orientation(str(data["orientation"])),
        )


class RitualDrawEngine:
    @staticmethod
    def _orientation(allow_reversed: bool = True) -> Orientation:
        if allow_reversed and secrets.randbelow(2) == 1:
            return Orientation.REVERSED
        return Orientation.UPRIGHT

    @staticmethod
    def _available_cards(excluded_codes: set[str]) -> list[TarotCard]:
        cards = [
            card
            for card in tarot_draw_service.list_cards()
            if card.code not in excluded_codes
        ]
        if not cards:
            raise ValueError("No cards remain available in the deck.")
        return cards

    def draw_one(
        self,
        *,
        position: SpreadPosition,
        excluded_codes: set[str],
        allow_reversed: bool = True,
    ) -> DrawnCard:
        available = self._available_cards(excluded_codes)
        card = available[secrets.randbelow(len(available))]
        return DrawnCard(
            position=position,
            card=card,
            orientation=self._orientation(allow_reversed),
        )

    def should_cards_fall(
        self,
        *,
        draw_index: int,
        has_fallen_before: bool,
    ) -> bool:
        """Roll a random probability, then roll whether a fall occurs.

        First draw: probability itself is uniformly selected from 0..30%.
        Later draws: 0..8%.
        After any previous fall: 0..3%.
        Percentages are sampled in basis points so the internal probability is
        not exposed to the user.
        """
        if has_fallen_before:
            max_basis_points = 700
        elif draw_index == 0:
            max_basis_points = 6000
        else:
            max_basis_points = 2500

        probability_basis_points = secrets.randbelow(max_basis_points + 1)
        return secrets.randbelow(10000) < probability_basis_points

    def fallen_candidates(
        self,
        *,
        excluded_codes: set[str],
        allow_reversed: bool = True,
    ) -> list[FallenCandidate]:
        amount = 2 + secrets.randbelow(3)
        available = self._available_cards(excluded_codes)
        if len(available) < amount:
            amount = len(available)

        candidates: list[FallenCandidate] = []
        pool = list(available)
        for _ in range(amount):
            card = pool.pop(secrets.randbelow(len(pool)))
            candidates.append(
                FallenCandidate(
                    card_code=card.code,
                    orientation=self._orientation(allow_reversed),
                )
            )
        return candidates

    @staticmethod
    def materialize_candidate(
        *,
        candidate: FallenCandidate,
        position: SpreadPosition,
    ) -> DrawnCard:
        card = next(
            (
                item
                for item in tarot_draw_service.list_cards()
                if item.code == candidate.card_code
            ),
            None,
        )
        if card is None:
            raise ValueError(f"Unknown candidate card: {candidate.card_code}")
        return DrawnCard(
            position=position,
            card=card,
            orientation=candidate.orientation,
        )


ritual_draw_engine = RitualDrawEngine()
