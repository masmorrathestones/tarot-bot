from app.tarot.models import Spread, SpreadPosition


THREE_CARD_SITUATION = Spread(
    code="THREE_CARD_SITUATION",
    name="Situação / Obstáculo / Tendência",
    description=(
        "Tiragem de três cartas para compreender o estado atual da questão, "
        "a principal dinâmica ou obstáculo e a tendência de desenvolvimento."
    ),
    positions=(
        SpreadPosition(
            index=1,
            code="CURRENT_SITUATION",
            name="Situação atual",
            description="Representa o estado atual e o núcleo da questão apresentada."
        ),
        SpreadPosition(
            index=2,
            code="OBSTACLE_OR_DYNAMIC",
            name="Obstáculo ou dinâmica",
            description=(
                "Representa a principal força, conflito, obstáculo ou dinâmica "
                "que influencia a situação."
            )
        ),
        SpreadPosition(
            index=3,
            code="TENDENCY",
            name="Tendência",
            description=(
                "Representa o desdobramento provável da situação caso as "
                "dinâmicas atuais permaneçam semelhantes."
            )
        ),
    ),
)


PAST_PRESENT_FUTURE = Spread(
    code="PAST_PRESENT_FUTURE",
    name="Passado / Presente / Futuro",
    description="Tiragem temporal clássica de três cartas.",
    positions=(
        SpreadPosition(
            index=1,
            code="PAST",
            name="Passado",
            description="Representa influências, causas ou acontecimentos anteriores."
        ),
        SpreadPosition(
            index=2,
            code="PRESENT",
            name="Presente",
            description="Representa a condição atual da situação."
        ),
        SpreadPosition(
            index=3,
            code="FUTURE",
            name="Futuro",
            description=(
                "Representa uma tendência futura, não uma previsão determinística."
            )
        ),
    ),
)


SELF_OTHER_RELATIONSHIP = Spread(
    code="SELF_OTHER_RELATIONSHIP",
    name="Eu / Outra pessoa / Relação",
    description="Tiragem de três cartas focada em vínculos e relações interpessoais.",
    positions=(
        SpreadPosition(
            index=1,
            code="SELF",
            name="Você",
            description="Representa a posição, energia ou perspectiva do consulente."
        ),
        SpreadPosition(
            index=2,
            code="OTHER",
            name="Outra pessoa",
            description=(
                "Representa simbolicamente a posição da outra pessoa na dinâmica, "
                "sem afirmar conhecer seus pensamentos ou intenções reais."
            )
        ),
        SpreadPosition(
            index=3,
            code="RELATIONSHIP",
            name="Relação",
            description="Representa a dinâmica emergente entre as duas partes."
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
