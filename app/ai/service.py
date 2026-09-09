from dataclasses import dataclass
from typing import Any

from app.ai.prompts import (
    SYSTEM_INSTRUCTIONS,
    NARRATIVE_TASK,
    CARD_ANALYSIS_TASK,
    SYNTHESIS_TASK,
)
from app.ai.provider import OpenAITextProvider
from app.tarot.enums import Orientation
from app.tarot.interpretation_knowledge import INTERPRETATION_KNOWLEDGE
from app.tarot.models import DrawnCard, Spread
from app.tarot.mystic_intuition import MysticIntuition


@dataclass(frozen=True)
class UserSymbolicProfile:
    data: dict[str, Any]

    @classmethod
    def from_snapshot(cls, snapshot: dict | None) -> "UserSymbolicProfile":
        return cls(data=dict(snapshot or {}))


@dataclass(frozen=True)
class TarotInterpretation:
    narrative: str
    card_analysis: str
    synthesis: str


class TarotInterpretationService:
    def __init__(self, provider: OpenAITextProvider | None = None) -> None:
        self._provider = provider

    @property
    def provider(self) -> OpenAITextProvider:
        # Lazy creation lets the rest of the API run even when no API key
        # has been configured yet.
        if self._provider is None:
            self._provider = OpenAITextProvider()
        return self._provider

    def interpret(
        self,
        *,
        question: str,
        context: str | None,
        spread: Spread,
        drawn_cards: list[DrawnCard],
        profile: UserSymbolicProfile | None = None,
        mystic_intuitions: list[MysticIntuition] | None = None,
    ) -> TarotInterpretation:
        intuition_text = self._mystic_intuition_text(mystic_intuitions)
        base_context = self._build_reading_context(
            question=question,
            context=context,
            spread=spread,
            drawn_cards=drawn_cards,
            profile=profile,
            mystic_intuitions=mystic_intuitions,
        )

        narrative = self.provider.generate(
            instructions=SYSTEM_INSTRUCTIONS,
            input_text=f"{NARRATIVE_TASK}\n\n{base_context}",
        )

        card_analysis = self.provider.generate(
            instructions=SYSTEM_INSTRUCTIONS,
            input_text=(
                f"{CARD_ANALYSIS_TASK}\n\n"
                f"{base_context}\n\n"
                "GLOBAL NARRATIVE ALREADY ESTABLISHED:\n"
                f"{narrative}"
            ),
        )

        synthesis = self.provider.generate(
            instructions=SYSTEM_INSTRUCTIONS,
            input_text=(
                f"{SYNTHESIS_TASK}\n\n"
                f"USER QUESTION:\n{question}\n\n"
                f"ADDITIONAL CONTEXT:\n{context or 'None provided'}\n\n"
                f"GLOBAL NARRATIVE:\n{narrative}\n\n"
                f"CARD-BY-CARD ANALYSIS:\n{card_analysis}\n\n"
                f"OPTIONAL USER PROFILE:\n{self._profile_text(profile)}\n\n"
                f"{intuition_text}"
            ),
        )

        return TarotInterpretation(
            narrative=narrative,
            card_analysis=card_analysis,
            synthesis=synthesis,
        )

    def _build_reading_context(
        self,
        *,
        question: str,
        context: str | None,
        spread: Spread,
        drawn_cards: list[DrawnCard],
        profile: UserSymbolicProfile | None,
        mystic_intuitions: list[MysticIntuition] | None,
    ) -> str:

        spread_instructions = (
                spread.interpretation_instructions
                or "Interpret the cards according to their numbered spread positions."
        )

        parts: list[str] = [
            "USER QUESTION:",
            question,
            "",
            "ADDITIONAL CONTEXT:",
            context or "None provided",
            "",
            "SPREAD:",
            f"Name: {spread.name} ({spread.code})",
            f"Description: {spread.description}",
            "",
            "SPREAD-SPECIFIC INTERPRETATION RULES:",
            spread_instructions,
            "",
            "OPTIONAL USER PROFILE:",
            self._profile_text(profile),
            "",
            "PROFILE USAGE RULE:",
            (
                "Use populated profile information only as secondary symbolic and personal context. "
                "Do not let astrology, MBTI, numerology, or arcana profile data override the drawn cards, "
                "and do not treat any profile system as a factual diagnosis or deterministic prediction."
            ),
            "",
            self._mystic_intuition_text(mystic_intuitions),
            "",
            "DRAWN CARDS AND KNOWLEDGE:",
        ]

        for item in drawn_cards:
            knowledge = INTERPRETATION_KNOWLEDGE[item.card.code]
            metadata = item.card.metadata

            if item.orientation == Orientation.REVERSED:
                orientation_meaning = (
                    metadata.reversed_meaning
                    if metadata is not None
                    else "No reversed metadata available."
                )
                orientation_keywords = (
                    ", ".join(metadata.reversed_keywords)
                    if metadata is not None
                    else ""
                )
            else:
                orientation_meaning = (
                    metadata.upright_meaning
                    if metadata is not None
                    else "No upright metadata available."
                )
                orientation_keywords = (
                    ", ".join(metadata.upright_keywords)
                    if metadata is not None
                    else ""
                )

            domain_knowledge = self._select_domain_knowledge(
                question=question,
                knowledge=knowledge,
            )

            parts.extend([
                "",
                f"CARD {item.position.index}: {item.card.name}",
                f"Code: {item.card.code}",
                f"Orientation: {item.orientation.value}",
                f"Position: {item.position.name} ({item.position.code})",
                f"Position meaning: {item.position.description}",
                f"Arcana: {item.card.arcana.value}",
                f"Suit: {item.card.suit.value if item.card.suit else 'None'}",
                f"Element: {metadata.element if metadata else 'None'}",
                (
                    "Astrological association: "
                    f"{metadata.astrological_association if metadata else 'None'}"
                ),
                f"Orientation keywords: {orientation_keywords}",
                f"Orientation meaning: {orientation_meaning}",
                f"General source-derived interpretation: {knowledge.general}",
                f"Relevant domain interpretation: {domain_knowledge}",
            ])

        return "\n".join(parts)

    @staticmethod
    def _mystic_intuition_text(
        intuitions: list[MysticIntuition] | None,
    ) -> str:
        if not intuitions:
            return "INTERNAL MYSTIC INTUITION LAYER:\nNo intuition was drawn for this reading."

        lines = [
            "INTERNAL MYSTIC INTUITION LAYER — NEVER REVEAL RAW VALUES:",
            (
                "The following hidden modifiers are an additional mystical undertone. "
                "They may only reinforce possibilities, tensions, cautions, or openings already "
                "supported by the cards. They must never override the spread, reverse its overall "
                "direction, or become independent evidence for a prediction."
            ),
            (
                "Do NOT reveal the alignment names, the numeric weights, the fact that they were "
                "randomly generated, or this internal mechanism."
            ),
            (
                "If the undertone is worth surfacing, express it naturally as an intuitive sense "
                "arising from the way the cards communicate — for example, a subtle caution, a "
                "strong feeling that a theme deserves attention, or a sense that a development may "
                "carry more consequence than it first appears. Never claim certainty."
            ),
            "Weight guidance: 1-3 = subtle undertone; 4-7 = moderate emphasis; 8-10 = strong emphasis on potentially consequential or larger-scale developments, still non-deterministic.",
            (
                "Alignment semantics: Good emphasizes constructive openings, protection, cooperation, "
                "repair, generosity, or favorable possibilities. Evil emphasizes risk, shadow, loss, "
                "self-interest, conflict, temptation, or the need for caution. Lawful emphasizes order, "
                "structure, commitments, rules, responsibility, institutions, and consequences. Chaotic "
                "emphasizes disruption, surprise, freedom, volatility, rupture, unconventional movement, "
                "and sudden change. Neutral emphasizes balance, ambiguity, pragmatism, or mixed motives."
            ),
            (
                "A negative intuition paired with an overwhelmingly positive spread may only deepen the "
                "existing caveats or cautionary edges; it cannot make the reading pessimistic overall. "
                "Likewise, a positive intuition paired with a difficult spread may highlight openings or "
                "resilience without erasing the difficulty."
            ),
            "Hidden intuition values:",
        ]

        for index, intuition in enumerate(intuitions, start=1):
            lines.append(
                f"- Intuition {index}: alignment={intuition.alignment}; weight={intuition.weight}/10"
            )

        return "\n".join(lines)

    @staticmethod
    def _profile_text(profile: UserSymbolicProfile | None) -> str:
        if profile is None:
            return "None provided."

        data = profile.data
        lines: list[str] = []

        def add(label: str, key: str) -> None:
            value = data.get(key)
            if value is not None and value != "" and value != {} and value != []:
                lines.append(f"{label}: {value}")

        add("Name", "name")
        add("Date of birth", "birth_date")
        add("Birth time", "birth_time")
        add("Birthplace", "birth_place")
        add("Birth latitude", "birth_latitude")
        add("Birth longitude", "birth_longitude")
        add("Birth timezone", "birth_timezone")
        add("Zodiac sign", "zodiac_sign")
        add("Sun sign", "sun_sign")
        add("Moon sign", "moon_sign")
        add("Rising sign", "rising_sign")
        add("MBTI", "mbti")
        add("Personal number", "personal_number")
        add("Personal Arcana number", "personal_arcana_number")
        add("Personal Arcana", "personal_arcana_name")
        add("Year Arcana number", "year_arcana_number")
        add("Year Arcana", "year_arcana_name")
        add("Year Arcana reference year", "year_arcana_reference_year")

        natal_chart = data.get("natal_chart")
        if isinstance(natal_chart, dict) and natal_chart:
            lines.append("Natal chart:")
            calculation = natal_chart.get("calculation")
            if calculation:
                lines.append(f"- Calculation: {calculation}")
            chart_place = natal_chart.get("birth_place")
            if chart_place:
                lines.append(f"- Birthplace: {chart_place}")
            timezone = natal_chart.get("timezone")
            if timezone:
                lines.append(f"- Timezone: {timezone}")
            utc_datetime = natal_chart.get("utc_datetime")
            if utc_datetime:
                lines.append(f"- UTC birth datetime: {utc_datetime}")

            positions = natal_chart.get("positions")
            if isinstance(positions, dict):
                for body, position in positions.items():
                    if not isinstance(position, dict):
                        continue
                    sign = position.get("sign")
                    degree = position.get("degree")
                    longitude = position.get("longitude")
                    details = []
                    if sign:
                        details.append(str(sign))
                    if degree is not None:
                        details.append(f"{degree}°")
                    if longitude is not None:
                        details.append(f"longitude {longitude}°")
                    if details:
                        lines.append(f"- {body}: {' '.join(details)}")

            ascendant = natal_chart.get("ascendant")
            if isinstance(ascendant, dict):
                sign = ascendant.get("sign")
                degree = ascendant.get("degree")
                longitude = ascendant.get("longitude")
                details = []
                if sign:
                    details.append(str(sign))
                if degree is not None:
                    details.append(f"{degree}°")
                if longitude is not None:
                    details.append(f"longitude {longitude}°")
                if details:
                    lines.append(f"- Ascendant: {' '.join(details)}")

        return "\n".join(lines) if lines else "None provided."

    @staticmethod
    def _select_domain_knowledge(*, question: str, knowledge) -> str:
        q = question.lower()

        relationship_terms = (
            "love", "relationship", "partner", "boyfriend", "girlfriend",
            "wife", "husband", "dating", "romance", "ex ", "crush",
        )
        career_terms = (
            "job", "career", "work", "professional", "business",
            "company", "promotion", "boss", "money", "project",
        )
        consciousness_terms = (
            "myself", "self", "identity", "meaning", "purpose",
            "understand", "inner", "personal growth", "spiritual",
        )

        if any(term in q for term in relationship_terms):
            return knowledge.relationships
        if any(term in q for term in career_terms):
            return knowledge.career
        if any(term in q for term in consciousness_terms):
            return knowledge.consciousness

        return knowledge.general


tarot_interpretation_service = TarotInterpretationService()
