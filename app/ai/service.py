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
                f"{CARD_ANALYSIS_TASK}\n\n{base_context}\n\n"
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
            "USER QUESTION:", question,
            "", "ADDITIONAL CONTEXT:", context or "None provided",
            "", "SPREAD:",
            f"Name: {spread.name} ({spread.code})",
            f"Description: {spread.description}",
            "", "SPREAD-SPECIFIC INTERPRETATION RULES:", spread_instructions,
            "", "OPTIONAL USER PROFILE:", self._profile_text(profile),
            "", "PROFILE AND PERSONALIZATION USAGE RULE:",
            (
                "Use profile data and selected relevant user information only as secondary context that may enrich the reading. "
                "Do not force the reading to focus on those facts and do not let astrology, MBTI, numerology, arcana profile data, "
                "or saved profile-analysis material override the drawn cards."
            ),
            "", self._symbolic_signal_text(profile),
            "", self._mystic_intuition_text(mystic_intuitions),
            "", "DRAWN CARDS AND KNOWLEDGE:",
        ]

        for item in drawn_cards:
            knowledge = INTERPRETATION_KNOWLEDGE[item.card.code]
            metadata = item.card.metadata
            if item.orientation == Orientation.REVERSED:
                orientation_meaning = metadata.reversed_meaning if metadata else "No reversed metadata available."
                orientation_keywords = ", ".join(metadata.reversed_keywords) if metadata else ""
            else:
                orientation_meaning = metadata.upright_meaning if metadata else "No upright metadata available."
                orientation_keywords = ", ".join(metadata.upright_keywords) if metadata else ""

            domain_knowledge = self._select_domain_knowledge(question=question, knowledge=knowledge)
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
                f"Astrological association: {metadata.astrological_association if metadata else 'None'}",
                f"Orientation keywords: {orientation_keywords}",
                f"Orientation meaning: {orientation_meaning}",
                f"General source-derived interpretation: {knowledge.general}",
                f"Relevant domain interpretation: {domain_knowledge}",
            ])
        return "\n".join(parts)

    @staticmethod
    def _symbolic_signal_text(profile: UserSymbolicProfile | None) -> str:
        signals = profile.data.get("symbolic_signals") if profile else None
        if not isinstance(signals, list) or not signals:
            return "DETERMINISTIC SYMBOLIC RECURRENCE SIGNALS:\nNone detected."

        lines = [
            "DETERMINISTIC SYMBOLIC RECURRENCE SIGNALS — THESE WERE COMPUTED BY APPLICATION CODE, NOT BY AI:",
            (
                "Treat each signal below as real metadata about this user's recorded Tarot history/profile. "
                "Do not recompute it, infer additional history, or ask for raw history. Mention every listed signal naturally in the user-facing analysis "
                "and let it have a meaningful symbolic effect. A Personal Arcana or Year Arcana match is especially important and should be treated as a major interpretive emphasis, while still remaining non-deterministic."
            ),
        ]
        for signal in signals:
            if isinstance(signal, dict) and signal.get("message"):
                lines.append(f"- {signal['message']}")
        return "\n".join(lines)

    @staticmethod
    def _mystic_intuition_text(
        intuitions: list[MysticIntuition] | None,
    ) -> str:
        if not intuitions:
            return "INTERNAL MYSTIC INTUITION LAYER:\nNo intuition was drawn for this reading."

        lines = [
            "INTERNAL MYSTIC INTUITION LAYER — NEVER REVEAL RAW VALUES:",
            (
                "These hidden modifiers are interpretive undertones. They may reinforce possibilities, tensions, cautions, or openings already supported by the cards. "
                "Never reveal alignment labels, numeric weights, randomization, or the internal mechanism."
            ),
            (
                "Use each intuition's mapped meaning as an instruction for HOW that intuition should influence the analysis. "
                "The mapped meaning is authoritative for that alignment, but it still cannot reverse an overwhelmingly contrary spread or create unsupported facts."
            ),
            (
                "Weight guidance: 1-3 subtle; 4-7 moderate; 8-10 strong. When a high-weight intuition coheres with the cards, increase assertiveness substantially while avoiding absolute certainty."
            ),
            "Hidden intuition values and mapped meanings:",
        ]
        for index, intuition in enumerate(intuitions, start=1):
            lines.append(
                f"- Intuition {index}: alignment={intuition.alignment}; weight={intuition.weight}/10; meaning={intuition.description}"
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
        add("Saved profile analysis reference year", "profile_analysis_reference_year")
        add("Saved profile analysis summary", "profile_analysis_summary")

        relevant = data.get("selected_relevant_information")
        if isinstance(relevant, list) and relevant:
            lines.append("Selected relevant user information for this reading (optional supporting context; do not force focus):")
            lines.extend(f"- {value}" for value in relevant if value)

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
                    details = []
                    if position.get("sign"):
                        details.append(str(position["sign"]))
                    if position.get("degree") is not None:
                        details.append(f"{position['degree']}°")
                    if position.get("longitude") is not None:
                        details.append(f"longitude {position['longitude']}°")
                    if details:
                        lines.append(f"- {body}: {' '.join(details)}")
            ascendant = natal_chart.get("ascendant")
            if isinstance(ascendant, dict):
                details = []
                if ascendant.get("sign"):
                    details.append(str(ascendant["sign"]))
                if ascendant.get("degree") is not None:
                    details.append(f"{ascendant['degree']}°")
                if ascendant.get("longitude") is not None:
                    details.append(f"longitude {ascendant['longitude']}°")
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
