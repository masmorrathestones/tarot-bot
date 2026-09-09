from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from datetime import date


ARCANA = {
    1: ("The Magician", "A mission of initiative and creation. It asks for self-confidence to turn ideas into action; the challenge is usually focusing your energy instead of scattering it."),
    2: ("The High Priestess", "A mission connected to intuition and inner wisdom. It tends to ask you to trust your own voice before seeking external validation."),
    3: ("The Empress", "A mission of creating, nurturing, and generating abundance. The challenge is balancing care for others with care for yourself."),
    4: ("The Emperor", "A mission of structure and leadership. It often asks for firmness while avoiding rigidity."),
    5: ("The Hierophant", "A mission of learning and transmitting knowledge. It tends to value faith and ethics without becoming trapped by dogma."),
    6: ("The Lovers", "A mission of conscious choices and meaningful bonds. The central challenge is clarity in the face of indecision."),
    7: ("The Chariot", "A mission of determination and achievement. It asks for focus to move forward without overriding your own pace."),
    8: ("Justice", "A mission of balance and ethical decisions. It tends to ask you to reconcile reason and sensitivity."),
    9: ("The Hermit", "A mission of reflection and self-knowledge. The challenge is seeking inner silence without becoming excessively isolated."),
    10: ("Wheel of Fortune", "A mission of learning through cycles. It often asks for trust when circumstances change direction."),
    11: ("Strength", "A mission of courage and inner mastery. It tends to work through patience and gentle firmness."),
    12: ("The Hanged Man", "A mission of seeing life from different angles. The challenge is accepting pauses without falling into stagnation."),
    13: ("Death", "A mission of transformation and new beginnings. It asks for courage to close cycles that have already fulfilled their role."),
    14: ("Temperance", "A mission of balance and moderation. It often asks for harmony between extremes and patience with the timing of things."),
    15: ("The Devil", "A mission of dealing with desires and attachments. The challenge is recognizing what binds you and becoming freer with awareness."),
    16: ("The Tower", "A mission of building, breaking, and rebuilding. It tends to ask for resilience in the face of sudden change."),
    17: ("The Star", "A mission of hope and purpose. It often asks you to care for your own light and your aspirations."),
    18: ("The Moon", "A mission of entering deeply into emotion and intuition. The challenge is distinguishing reality from illusion."),
    19: ("The Sun", "A mission of radiating joy and vitality. It tends to ask for depth beyond appearances."),
    20: ("Judgement", "A mission of awakening and renewal. It often asks you to listen to a larger calling and resolve unfinished matters."),
    21: ("The World", "A mission of fulfillment and integration. It asks you to integrate what you have learned and complete major cycles."),
    22: ("The Fool", "A mission of freedom and new beginnings. The challenge is balancing boldness with responsibility."),
}

ZODIAC_DESCRIPTIONS = {
    "Aries": "Aries is associated with initiative, courage, and the impulse to begin. It tends to act directly and energetically, with the challenge of balancing speed and patience.",
    "Taurus": "Taurus is associated with stability, sensory experience, and perseverance. It values security and consistency, with the challenge of not turning firmness into resistance to change.",
    "Gemini": "Gemini is associated with curiosity, communication, and versatility. It seeks movement and exchange of ideas, with the challenge of maintaining focus and depth.",
    "Cancer": "Cancer is associated with sensitivity, protection, and emotional bonds. It values belonging and memory, with the challenge of caring without retreating behind defenses.",
    "Leo": "Leo is associated with expression, creativity, and vitality. It seeks to radiate presence and affection, with the challenge of balancing external recognition and inner confidence.",
    "Virgo": "Virgo is associated with analysis, organization, and refinement. It tends to notice details and serve in practical ways, with the challenge of softening self-criticism.",
    "Libra": "Libra is associated with harmony, relationships, and a sense of balance. It seeks to reconcile perspectives, with the challenge of not postponing choices merely to avoid conflict.",
    "Scorpio": "Scorpio is associated with intensity, transformation, and emotional depth. It tends to investigate what is hidden, with the challenge of dealing with control and letting go.",
    "Sagittarius": "Sagittarius is associated with expansion, the search for meaning, and freedom. It values experience and broad horizons, with the challenge of balancing enthusiasm and commitment.",
    "Capricorn": "Capricorn is associated with discipline, responsibility, and long-term construction. It seeks consistent results, with the challenge of not reducing life to duties alone.",
    "Aquarius": "Aquarius is associated with independence, originality, and collective vision. It tends to question established patterns, with the challenge of balancing rational distance and emotional connection.",
    "Pisces": "Pisces is associated with imagination, empathy, and symbolic sensitivity. It notices nuances and atmospheres, with the challenge of maintaining boundaries and clarity around emotions.",
}


@dataclass(frozen=True)
class PersonalArcanaResult:
    personal_number: int
    personal_arcana_name: str
    personal_arcana_description: str
    year_arcana_number: int
    year_arcana_name: str
    year_arcana_description: str
    reference_year: int


def reduce_to_arcana(value: int) -> int:
    while value > 22:
        value = sum(int(digit) for digit in str(value))
    return value


def name_value(name: str) -> int:
    normalized = unicodedata.normalize("NFKD", name)
    letters = [c.upper() for c in normalized if c.isascii() and c.isalpha()]
    return sum(ord(letter) - ord("A") + 1 for letter in letters)


def digit_sum(value: str) -> int:
    return sum(int(char) for char in value if char.isdigit())


def calculate_personal_arcana(name: str, birth_date: date, reference_year: int | None = None) -> PersonalArcanaResult:
    year = reference_year or date.today().year
    reduced_name = reduce_to_arcana(name_value(name))
    birth_sum = digit_sum(birth_date.strftime("%d%m%Y"))
    personal_number = reduce_to_arcana(reduced_name + birth_sum)
    year_number = reduce_to_arcana(birth_sum + digit_sum(str(year)))

    personal_name, personal_description = ARCANA[personal_number]
    year_name, year_description = ARCANA[year_number]
    return PersonalArcanaResult(
        personal_number=personal_number,
        personal_arcana_name=personal_name,
        personal_arcana_description=personal_description,
        year_arcana_number=year_number,
        year_arcana_name=year_name,
        year_arcana_description=year_description,
        reference_year=year,
    )


def zodiac_for_birth_date(birth_date: date) -> tuple[str, str]:
    month_day = (birth_date.month, birth_date.day)
    boundaries = [
        ((1, 20), "Aquarius"), ((2, 19), "Pisces"), ((3, 21), "Aries"),
        ((4, 20), "Taurus"), ((5, 21), "Gemini"), ((6, 21), "Cancer"),
        ((7, 23), "Leo"), ((8, 23), "Virgo"), ((9, 23), "Libra"),
        ((10, 23), "Scorpio"), ((11, 22), "Sagittarius"), ((12, 22), "Capricorn"),
    ]
    sign = "Capricorn"
    for boundary, candidate in boundaries:
        if month_day >= boundary:
            sign = candidate
    return sign, ZODIAC_DESCRIPTIONS[sign]
