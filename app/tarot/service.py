import secrets

from app.tarot.deck import RIDER_WAITE_DECK
from app.tarot.enums import Orientation
from app.tarot.models import DrawnCard, Spread, TarotCard
from app.tarot.spreads import SPREADS
from app.tarot.interpretation_knowledge import INTERPRETATION_KNOWLEDGE


class TarotDrawService:
    def __init__(self) -> None:
        self.deck = RIDER_WAITE_DECK

    def list_cards(self) -> list[TarotCard]:
        return list(self.deck)

    def list_spreads(self) -> list[Spread]:
        return list(SPREADS.values())

    def get_spread(self, spread_code: str) -> Spread | None:
        return SPREADS.get(spread_code.upper())


    def get_interpretation_knowledge(self, card_code: str):
        return INTERPRETATION_KNOWLEDGE.get(card_code.upper())

    def draw(self, spread: Spread, allow_reversed: bool = True) -> list[DrawnCard]:
        amount = len(spread.positions)

        if amount > len(self.deck):
            raise ValueError(
                f"spread requests {amount} cards, but deck has only {len(self.deck)}"
            )

        available_cards = list(self.deck)
        drawn_cards: list[DrawnCard] = []

        for position in spread.positions:
            card_index = secrets.randbelow(len(available_cards))
            card = available_cards.pop(card_index)

            orientation = Orientation.UPRIGHT

            if allow_reversed and secrets.randbelow(2) == 1:
                orientation = Orientation.REVERSED

            drawn_cards.append(
                DrawnCard(
                    position=position,
                    card=card,
                    orientation=orientation
                )
            )

        return drawn_cards


tarot_draw_service = TarotDrawService()
