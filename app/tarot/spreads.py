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

THE_PATH = Spread(
    code="THE_PATH",
    name="The Path",
    description=(
        "A seven-card guidance spread for questions about how the querent "
        "should approach a situation. It contrasts the current conscious, "
        "emotional, and outward attitudes with constructive future attitudes."
    ),
    positions=(
        SpreadPosition(
            index=1,
            code="SUBJECT",
            name="Subject",
            description=(
                "Represents the central issue, including the opportunities "
                "and risks involved in the question."
            ),
        ),
        SpreadPosition(
            index=2,
            code="CURRENT_CONSCIOUS_ATTITUDE",
            name="Current conscious attitude",
            description=(
                "Represents the querent's current rational attitude: thoughts, "
                "intentions, conscious motivations, and mental approach."
            ),
        ),
        SpreadPosition(
            index=3,
            code="CURRENT_EMOTIONAL_ATTITUDE",
            name="Current emotional attitude",
            description=(
                "Represents the querent's current inner and emotional attitude: "
                "desires, hopes, fears, longings, and unconscious motivations."
            ),
        ),
        SpreadPosition(
            index=4,
            code="CURRENT_OUTWARD_ATTITUDE",
            name="Current outward attitude",
            description=(
                "Represents how the querent currently acts, presents themselves, "
                "or behaves outwardly in relation to the issue."
            ),
        ),
        SpreadPosition(
            index=5,
            code="PROPOSED_OUTWARD_ATTITUDE",
            name="Proposed outward attitude",
            description=(
                "Suggests how the querent could act or present themselves "
                "outwardly going forward."
            ),
        ),
        SpreadPosition(
            index=6,
            code="PROPOSED_EMOTIONAL_ATTITUDE",
            name="Proposed emotional attitude",
            description=(
                "Suggests a constructive emotional or inner attitude toward "
                "the situation going forward."
            ),
        ),
        SpreadPosition(
            index=7,
            code="PROPOSED_CONSCIOUS_ATTITUDE",
            name="Proposed conscious attitude",
            description=(
                "Suggests a constructive rational perspective, intention, "
                "or conscious strategy going forward."
            ),
        ),
    ),
)


THE_CROSS = Spread(
    code="THE_CROSS",
    name="The Cross",
    description=(
        "A four-card guidance spread for identifying the central issue, "
        "an approach to avoid, an approach to favor, and the resulting direction."
    ),
    positions=(
        SpreadPosition(
            index=1,
            code="SUBJECT",
            name="Subject",
            description="Represents the central theme or issue.",
        ),
        SpreadPosition(
            index=2,
            code="PATH_TO_AVOID",
            name="Path to avoid",
            description=(
                "Represents an approach that may appear attractive but should "
                "not be followed, or a challenge that should not dictate the response."
            ),
        ),
        SpreadPosition(
            index=3,
            code="CONSTRUCTIVE_PATH",
            name="Constructive path",
            description=(
                "Represents the approach that is more appropriate or constructive "
                "for dealing with the issue."
            ),
        ),
        SpreadPosition(
            index=4,
            code="DIRECTION",
            name="Direction",
            description=(
                "Represents the direction toward which the situation develops "
                "when approached constructively."
            ),
        ),
    ),
)


BLIND_SPOT = Spread(
    code="BLIND_SPOT",
    name="Blind Spot",
    description=(
        "A four-card self-knowledge spread inspired by the Johari Window, "
        "contrasting what is known and unknown to the querent and to others."
    ),
    positions=(
        SpreadPosition(
            index=1,
            code="KNOWN_IDENTITY",
            name="Known identity",
            description=(
                "Represents aspects of the self that are recognized both by "
                "the querent and by others."
            ),
        ),
        SpreadPosition(
            index=2,
            code="GREAT_UNKNOWN",
            name="The great unknown",
            description=(
                "Represents unconscious processes that are recognized neither "
                "by the querent nor by others."
            ),
        ),
        SpreadPosition(
            index=3,
            code="HIDDEN_SELF",
            name="Hidden self",
            description=(
                "Represents aspects the querent recognizes in themselves but "
                "conceals or does not reveal to others."
            ),
        ),
        SpreadPosition(
            index=4,
            code="BLIND_SPOT",
            name="Blind spot",
            description=(
                "Represents qualities or behaviors others may perceive in the "
                "querent while the querent does not consciously recognize them."
            ),
        ),
    ),
)

RELATIONSHIP_SPREAD = Spread(
    code="RELATIONSHIP_SPREAD",
    name="Relationship",
    description=(
        "A seven-card spread for examining how two people meet within a "
        "relationship across conscious, emotional, and outward levels."
    ),
    positions=(
        SpreadPosition(
            index=1,
            code="RELATIONSHIP_THEME",
            name="Relationship theme",
            description=(
                "Represents the current state and central theme governing "
                "the relationship."
            ),
        ),
        SpreadPosition(
            index=2,
            code="OTHER_CONSCIOUS",
            name="Other person's conscious position",
            description=(
                "Symbolically represents the other side's conscious position "
                "within the relationship, without asserting their private thoughts."
            ),
        ),
        SpreadPosition(
            index=3,
            code="OTHER_EMOTIONAL",
            name="Other person's emotional position",
            description=(
                "Symbolically represents the emotional or perceptive dimension "
                "of the other side of the relationship, without claiming hidden facts."
            ),
        ),
        SpreadPosition(
            index=4,
            code="OTHER_OUTWARD",
            name="Other person's outward position",
            description=(
                "Represents how the other side appears or functions outwardly "
                "within the relationship dynamic."
            ),
        ),
        SpreadPosition(
            index=5,
            code="SELF_OUTWARD",
            name="Your outward position",
            description=(
                "Represents how the querent acts or presents themselves outwardly "
                "within the relationship."
            ),
        ),
        SpreadPosition(
            index=6,
            code="SELF_EMOTIONAL",
            name="Your emotional position",
            description=(
                "Represents the querent's feelings, perceptions, hopes, fears, "
                "or emotional experience of the relationship."
            ),
        ),
        SpreadPosition(
            index=7,
            code="SELF_CONSCIOUS",
            name="Your conscious position",
            description=(
                "Represents what the querent consciously thinks, intends, or "
                "believes about the relationship."
            ),
        ),
    ),
)

DECISION_SPREAD = Spread(
    code="DECISION_SPREAD",
    name="Decision",
    description=(
        "A seven-card spread comparing the development of taking a particular "
        "course of action with the development of not taking it. It does not "
        "reduce the reading to a deterministic yes-or-no answer."
    ),
    interpretation_instructions=(
        "IMPORTANT: Do not interpret this spread as a linear sequence "
        "1 → 2 → 3 → 4 → 5 → 6 → 7. "
        "Card 7 is the significator and represents the decision itself. "
        "There are two separate temporal paths. "
        "If the action is taken, read cards 5 → 1 → 3 in that order. "
        "If the action is not taken, read cards 6 → 2 → 4 in that order. "
        "Compare these two paths as parallel alternatives. "
        "For the visual narrative, analyze visual movement inside each path "
        "separately before comparing the two paths."
    ),
    positions=(
        SpreadPosition(
            index=1,
            code="ACTION_MIDDLE",
            name="If you do it — development",
            description=(
                "Represents the middle stage of the path that follows if the "
                "querent takes the proposed action."
            ),
        ),
        SpreadPosition(
            index=2,
            code="INACTION_MIDDLE",
            name="If you don't — development",
            description=(
                "Represents the middle stage of the path that follows if the "
                "querent does not take the proposed action."
            ),
        ),
        SpreadPosition(
            index=3,
            code="ACTION_OUTCOME",
            name="If you do it — later tendency",
            description=(
                "Represents the later tendency of the path in which the proposed "
                "action is taken."
            ),
        ),
        SpreadPosition(
            index=4,
            code="INACTION_OUTCOME",
            name="If you don't — later tendency",
            description=(
                "Represents the later tendency of the path in which the proposed "
                "action is not taken."
            ),
        ),
        SpreadPosition(
            index=5,
            code="ACTION_BEGINNING",
            name="If you do it — first development",
            description=(
                "Represents the first stage of the path in which the proposed "
                "action is taken."
            ),
        ),
        SpreadPosition(
            index=6,
            code="INACTION_BEGINNING",
            name="If you don't — first development",
            description=(
                "Represents the first stage of the path in which the proposed "
                "action is not taken."
            ),
        ),
        SpreadPosition(
            index=7,
            code="DECISION_SIGNIFICATOR",
            name="Decision significator",
            description=(
                "Represents the meaning of the decision itself, the central "
                "problem, or the querent's position toward the choice."
            ),
        ),
    ),
)

CELTIC_CROSS = Spread(
    code="CELTIC_CROSS",
    name="Celtic Cross",
    description=(
        "A comprehensive ten-card spread for examining a situation, its causes, "
        "conscious and unconscious factors, environment, expectations, and "
        "short- and longer-term tendencies."
    ),
    positions=(
        SpreadPosition(
            index=1,
            code="STARTING_SITUATION",
            name="Starting situation",
            description="Represents the central situation or subject of the question.",
        ),
        SpreadPosition(
            index=2,
            code="CROSSING_INFLUENCE",
            name="Crossing influence",
            description=(
                "Represents an additional force that may help the situation "
                "progress or create an obstacle."
            ),
        ),
        SpreadPosition(
            index=3,
            code="CONSCIOUS_LEVEL",
            name="Conscious level",
            description=(
                "Represents what the querent consciously recognizes, understands, "
                "seeks, or promotes in the situation."
            ),
        ),
        SpreadPosition(
            index=4,
            code="UNCONSCIOUS_FOUNDATION",
            name="Unconscious foundation",
            description=(
                "Represents the deeper emotional or unconscious foundation on "
                "which the situation rests."
            ),
        ),
        SpreadPosition(
            index=5,
            code="DISTANT_PAST",
            name="Distant past and causes",
            description=(
                "Represents more distant past influences and causes that contributed "
                "to the present situation."
            ),
        ),
        SpreadPosition(
            index=6,
            code="NEAR_FUTURE",
            name="Near future",
            description=(
                "Represents the next likely stage or near-future tendency."
            ),
        ),
        SpreadPosition(
            index=7,
            code="QUERENT_POSITION",
            name="Your position",
            description=(
                "Represents the querent's attitude toward the issue and how "
                "they experience their position within it."
            ),
        ),
        SpreadPosition(
            index=8,
            code="ENVIRONMENT",
            name="Environment",
            description=(
                "Represents the surrounding circumstances, setting, or influence "
                "of other people."
            ),
        ),
        SpreadPosition(
            index=9,
            code="HOPES_AND_FEARS",
            name="Hopes and fears",
            description=(
                "Represents the querent's expectations, hopes, anxieties, or fears; "
                "it is not itself a prediction."
            ),
        ),
        SpreadPosition(
            index=10,
            code="LONG_TERM_TENDENCY",
            name="Long-term tendency",
            description=(
                "Represents the more distant development and the direction toward "
                "which the matter may be moving."
            ),
        ),
    ),
)

HIGH_PRIESTESS_SECRET = Spread(
    code="HIGH_PRIESTESS_SECRET",
    name="The High Priestess's Secret",
    description=(
        "A nine-card spread for exploring interacting forces around a question, "
        "what is increasing or decreasing in influence, what is conscious or hidden, "
        "and the direction in which the situation develops."
    ),
    positions=(
        SpreadPosition(
            index=1,
            code="SUBJECT",
            name="Subject",
            description="Represents one of the two principal forces defining the issue.",
        ),
        SpreadPosition(
            index=2,
            code="CROSSING_FORCE",
            name="Crossing force",
            description=(
                "Represents the second principal force, which may reinforce or "
                "conflict with the first."
            ),
        ),
        SpreadPosition(
            index=3,
            code="PRESENT_MAIN_INFLUENCE",
            name="Main present influence",
            description="Represents the strongest influence currently acting on the issue.",
        ),
        SpreadPosition(
            index=4,
            code="GROWING_INFLUENCE",
            name="Growing influence",
            description="Represents a force whose influence is increasing.",
        ),
        SpreadPosition(
            index=5,
            code="DECLINING_INFLUENCE",
            name="Declining influence",
            description="Represents a force whose influence is diminishing.",
        ),
        SpreadPosition(
            index=6,
            code="HIDDEN",
            name="What is hidden",
            description=(
                "Represents something present in the situation but not clearly "
                "recognized consciously."
            ),
        ),
        SpreadPosition(
            index=7,
            code="KNOWN",
            name="What is known",
            description=(
                "Represents what is consciously recognized, understood, or evaluated."
            ),
        ),
        SpreadPosition(
            index=8,
            code="NEXT_DIRECTION",
            name="Where the journey goes",
            description="Represents what comes next and the direction of development.",
        ),
        SpreadPosition(
            index=9,
            code="SECRET",
            name="The secret",
            description=(
                "A final hidden card. In Banzhaf's method it reveals a deeper motive "
                "only if it is a Major Arcana; otherwise the secret remains unrevealed."
            ),
        ),
    ),
)

SPREADS = {
    spread.code: spread
    for spread in (
        THREE_CARD_SITUATION,
        PAST_PRESENT_FUTURE,
        SELF_OTHER_RELATIONSHIP,
        THE_PATH,
        THE_CROSS,
        BLIND_SPOT,
        RELATIONSHIP_SPREAD,
        DECISION_SPREAD,
        CELTIC_CROSS,
        HIGH_PRIESTESS_SECRET,
    )
}
