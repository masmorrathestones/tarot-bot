"""Translate persisted symbolic/profile labels to English.

Revision ID: 0007_english_profile_values
Revises: 0006_natal_chart
"""

from alembic import op
import sqlalchemy as sa


revision = "0007_english_profile_values"
down_revision = "0006_natal_chart"
branch_labels = None
depends_on = None


SIGN_MAP = {
    "Áries": "Aries",
    "Touro": "Taurus",
    "Gêmeos": "Gemini",
    "Câncer": "Cancer",
    "Leão": "Leo",
    "Virgem": "Virgo",
    "Libra": "Libra",
    "Escorpião": "Scorpio",
    "Sagitário": "Sagittarius",
    "Capricórnio": "Capricorn",
    "Aquário": "Aquarius",
    "Peixes": "Pisces",
}

ARCANA_MAP = {
    "O Mago": "The Magician",
    "A Sacerdotisa": "The High Priestess",
    "A Imperatriz": "The Empress",
    "O Imperador": "The Emperor",
    "O Papa": "The Hierophant",
    "Os Enamorados": "The Lovers",
    "O Carro": "The Chariot",
    "A Justiça": "Justice",
    "O Eremita": "The Hermit",
    "A Roda da Fortuna": "Wheel of Fortune",
    "A Força": "Strength",
    "O Enforcado": "The Hanged Man",
    "A Morte": "Death",
    "A Temperança": "Temperance",
    "O Diabo": "The Devil",
    "A Torre": "The Tower",
    "A Estrela": "The Star",
    "A Lua": "The Moon",
    "O Sol": "The Sun",
    "O Julgamento": "Judgement",
    "O Mundo": "The World",
    "O Louco": "The Fool",
}

PLANET_MAP = {
    "Sol": "Sun",
    "Lua": "Moon",
    "Mercúrio": "Mercury",
    "Vênus": "Venus",
    "Marte": "Mars",
    "Júpiter": "Jupiter",
    "Saturno": "Saturn",
    "Urano": "Uranus",
    "Netuno": "Neptune",
    "Plutão": "Pluto",
}

POSITION_MAP = {
    "CURRENT_SITUATION": (
        "Current situation",
        "Represents the current state and the core of the question presented.",
    ),
    "OBSTACLE_OR_DYNAMIC": (
        "Obstacle or dynamic",
        "Represents the main force, conflict, obstacle, or dynamic influencing the situation.",
    ),
    "TENDENCY": (
        "Tendency",
        "Represents the likely development of the situation if the current dynamics remain similar.",
    ),
    "PAST": ("Past", "Represents previous influences, causes, or events."),
    "PRESENT": ("Present", "Represents the current condition of the situation."),
    "FUTURE": ("Future", "Represents a future tendency, not a deterministic prediction."),
    "SELF": ("You", "Represents the querent's position, energy, or perspective."),
    "OTHER": (
        "Other person",
        "Symbolically represents the other person's position in the dynamic, without claiming knowledge of their actual thoughts or intentions.",
    ),
    "RELATIONSHIP": (
        "Relationship",
        "Represents the emerging dynamic between the two sides.",
    ),
}


def _translate_chart(chart):
    if not isinstance(chart, dict):
        return chart

    translated = dict(chart)
    positions = translated.get("positions")
    if isinstance(positions, dict):
        new_positions = {}
        for body, position in positions.items():
            body_name = PLANET_MAP.get(body, body)
            if isinstance(position, dict):
                new_position = dict(position)
                sign = new_position.get("sign")
                if sign in SIGN_MAP:
                    new_position["sign"] = SIGN_MAP[sign]
                new_positions[body_name] = new_position
            else:
                new_positions[body_name] = position
        translated["positions"] = new_positions

    ascendant = translated.get("ascendant")
    if isinstance(ascendant, dict):
        new_ascendant = dict(ascendant)
        sign = new_ascendant.get("sign")
        if sign in SIGN_MAP:
            new_ascendant["sign"] = SIGN_MAP[sign]
        translated["ascendant"] = new_ascendant

    return translated


def upgrade():
    bind = op.get_bind()

    profiles = sa.table(
        "user_profiles",
        sa.column("id", sa.Integer),
        sa.column("sun_sign", sa.String),
        sa.column("moon_sign", sa.String),
        sa.column("rising_sign", sa.String),
        sa.column("zodiac_sign", sa.String),
        sa.column("personal_arcana_name", sa.String),
        sa.column("year_arcana_name", sa.String),
        sa.column("natal_chart", sa.JSON),
    )

    rows = bind.execute(
        sa.select(
            profiles.c.id,
            profiles.c.sun_sign,
            profiles.c.moon_sign,
            profiles.c.rising_sign,
            profiles.c.zodiac_sign,
            profiles.c.personal_arcana_name,
            profiles.c.year_arcana_name,
            profiles.c.natal_chart,
        )
    ).mappings().all()

    for row in rows:
        values = {
            "sun_sign": SIGN_MAP.get(row["sun_sign"], row["sun_sign"]),
            "moon_sign": SIGN_MAP.get(row["moon_sign"], row["moon_sign"]),
            "rising_sign": SIGN_MAP.get(row["rising_sign"], row["rising_sign"]),
            "zodiac_sign": SIGN_MAP.get(row["zodiac_sign"], row["zodiac_sign"]),
            "personal_arcana_name": ARCANA_MAP.get(
                row["personal_arcana_name"], row["personal_arcana_name"]
            ),
            "year_arcana_name": ARCANA_MAP.get(
                row["year_arcana_name"], row["year_arcana_name"]
            ),
            "natal_chart": _translate_chart(row["natal_chart"]),
        }
        bind.execute(
            profiles.update().where(profiles.c.id == row["id"]).values(**values)
        )

    drawn_cards = sa.table(
        "drawn_cards",
        sa.column("position_code", sa.String),
        sa.column("position_name", sa.String),
        sa.column("position_description", sa.String),
    )
    for code, (name, description) in POSITION_MAP.items():
        bind.execute(
            drawn_cards.update()
            .where(drawn_cards.c.position_code == code)
            .values(position_name=name, position_description=description)
        )


def downgrade():
    # This migration standardizes persisted display values to English.
    # Downgrading the schema does not require restoring translated display text.
    pass
