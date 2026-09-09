from app.tarot.models import Spread, SpreadPosition


THREE_CARD_SITUATION = Spread(
    code="THREE_CARD_SITUATION",
    name="Situation / Obstacle / Tendency",
    description=(
        "A three-card spread for understanding the current state of the question, "
        "the main dynamic or obstacle, and the likely direction of development."
    ),
    positions=(
        SpreadPosition(
            index=1,
            code="CURRENT_SITUATION",
            name="Current situation",
            description="Represents the current state and the core of the question presented."
        ),
        SpreadPosition(
            index=2,
            code="OBSTACLE_OR_DYNAMIC",
            name="Obstacle or dynamic",
            description=(
                "Represents the main force, conflict, obstacle, or dynamic "
                "influencing the situation."
            )
        ),
        SpreadPosition(
            index=3,
            code="TENDENCY",
            name="Tendency",
            description=(
                "Represents the likely development of the situation if the "
                "current dynamics remain similar."
            )
        ),
    ),
)


PAST_PRESENT_FUTURE = Spread(
    code="PAST_PRESENT_FUTURE",
    name="Past / Present / Future",
    description="A classic three-card temporal spread.",
    positions=(
        SpreadPosition(
            index=1,
            code="PAST",
            name="Past",
            description="Represents previous influences, causes, or events."
        ),
        SpreadPosition(
            index=2,
            code="PRESENT",
            name="Present",
            description="Represents the current condition of the situation."
        ),
        SpreadPosition(
            index=3,
            code="FUTURE",
            name="Future",
            description=(
                "Represents a future tendency, not a deterministic prediction."
            )
        ),
    ),
)


SELF_OTHER_RELATIONSHIP = Spread(
    code="SELF_OTHER_RELATIONSHIP",
    name="You / Other person / Relationship",
    description="A three-card spread focused on bonds and interpersonal relationships.",
    positions=(
        SpreadPosition(
            index=1,
            code="SELF",
            name="You",
            description="Represents the querent's position, energy, or perspective."
        ),
        SpreadPosition(
            index=2,
            code="OTHER",
            name="Other person",
            description=(
                "Symbolically represents the other person's position in the dynamic, "
                "without claiming knowledge of their actual thoughts or intentions."
            )
        ),
        SpreadPosition(
            index=3,
            code="RELATIONSHIP",
            name="Relationship",
            description="Represents the emerging dynamic between the two sides."
        ),
    ),
)


SPREADS = {
    spread.code: spread
    for spread in (
        THREE_CARD_SITUATION,
        PAST_PRESENT_FUTURE,
        SELF_OTHER_RELATIONSHIP,
    )
}
