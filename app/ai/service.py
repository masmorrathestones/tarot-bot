from dataclasses import dataclass
from typing import Optional

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


@dataclass(frozen=True)
class UserSymbolicProfile:
    sun_sign: Optional[str] = None
    moon_sign: Optional[str] = None
    rising_sign: Optional[str] = None
    mbti: Optional[str] = None


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
    ) -> TarotInterpretation:
        base_context = self._build_reading_context(
            question=question,
            context=context,
            spread=spread,
            drawn_cards=drawn_cards,
            profile=profile,
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
                f"OPTIONAL USER PROFILE:\n{self._profile_text(profile)}"
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
    ) -> str:
        parts: list[str] = [
            "USER QUESTION:",
            question,
            "",
            "ADDITIONAL CONTEXT:",
            context or "None provided",
            "",
            "SPREAD:",
            f"{spread.name} ({spread.code})",
            spread.description,
            "",
            "OPTIONAL USER PROFILE:",
            self._profile_text(profile),
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
    def _profile_text(profile: UserSymbolicProfile | None) -> str:
        if profile is None:
            return "None provided."

        values = []
        if profile.sun_sign:
            values.append(f"Sun sign: {profile.sun_sign}")
        if profile.moon_sign:
            values.append(f"Moon sign: {profile.moon_sign}")
        if profile.rising_sign:
            values.append(f"Rising sign: {profile.rising_sign}")
        if profile.mbti:
            values.append(f"MBTI: {profile.mbti}")

        return "; ".join(values) if values else "None provided."

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
