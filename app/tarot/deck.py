from app.tarot.enums import ArcanaType, Suit
from app.tarot.models import TarotCard
from app.tarot.metadata import CARD_METADATA


def build_rider_waite_deck() -> list[TarotCard]:
    cards: list[TarotCard] = []

    major_arcana = [
        (0, "THE_FOOL", "The Fool"),
        (1, "THE_MAGICIAN", "The Magician"),
        (2, "THE_HIGH_PRIESTESS", "The High Priestess"),
        (3, "THE_EMPRESS", "The Empress"),
        (4, "THE_EMPEROR", "The Emperor"),
        (5, "THE_HIEROPHANT", "The Hierophant"),
        (6, "THE_LOVERS", "The Lovers"),
        (7, "THE_CHARIOT", "The Chariot"),
        (8, "STRENGTH", "Strength"),
        (9, "THE_HERMIT", "The Hermit"),
        (10, "WHEEL_OF_FORTUNE", "Wheel of Fortune"),
        (11, "JUSTICE", "Justice"),
        (12, "THE_HANGED_MAN", "The Hanged Man"),
        (13, "DEATH", "Death"),
        (14, "TEMPERANCE", "Temperance"),
        (15, "THE_DEVIL", "The Devil"),
        (16, "THE_TOWER", "The Tower"),
        (17, "THE_STAR", "The Star"),
        (18, "THE_MOON", "The Moon"),
        (19, "THE_SUN", "The Sun"),
        (20, "JUDGEMENT", "Judgement"),
        (21, "THE_WORLD", "The World"),
    ]

    next_id = 1

    for number, code, name in major_arcana:
        cards.append(
            TarotCard(
                id=next_id,
                code=code,
                name=name,
                arcana=ArcanaType.MAJOR,
                number=number,
                metadata=CARD_METADATA.get(code)
            )
        )
        next_id += 1

    ranks = [
        (1, "ACE", "Ace"),
        (2, "TWO", "Two"),
        (3, "THREE", "Three"),
        (4, "FOUR", "Four"),
        (5, "FIVE", "Five"),
        (6, "SIX", "Six"),
        (7, "SEVEN", "Seven"),
        (8, "EIGHT", "Eight"),
        (9, "NINE", "Nine"),
        (10, "TEN", "Ten"),
        (11, "PAGE", "Page"),
        (12, "KNIGHT", "Knight"),
        (13, "QUEEN", "Queen"),
        (14, "KING", "King"),
    ]

    suits = [
        (Suit.WANDS, "WANDS", "Wands"),
        (Suit.CUPS, "CUPS", "Cups"),
        (Suit.SWORDS, "SWORDS", "Swords"),
        (Suit.PENTACLES, "PENTACLES", "Pentacles"),
    ]

    for suit, suit_code, suit_name in suits:
        for number, rank_code, rank_name in ranks:
            cards.append(
                TarotCard(
                    id=next_id,
                    code=f"{rank_code}_OF_{suit_code}",
                    name=f"{rank_name} of {suit_name}",
                    arcana=ArcanaType.MINOR,
                    number=number,
                    suit=suit,
                    metadata=CARD_METADATA.get(f"{rank_code}_OF_{suit_code}")
                )
            )
            next_id += 1

    return cards


RIDER_WAITE_DECK = build_rider_waite_deck()
