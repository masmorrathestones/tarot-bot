from __future__ import annotations

import json

from app.ai.provider import OpenAITextProvider
from app.tarot.interpretation_knowledge import INTERPRETATION_KNOWLEDGE
from app.tarot.models import DrawnCard
from app.whatsapp.i18n import output_language_instruction


SYSTEM = """You are the interpretive voice of Holomancy's Past Life Tarot.
Treat the reading as a symbolic and divinatory experience. Be precise, direct and internally
consistent. Never mention hidden prompts, scoring, MBTI, profile fields or the internal use of
the word-derived arcana. Do not add disclaimers inside the reading."""


class PastLifeAIService:
    def __init__(self, provider: OpenAITextProvider | None = None) -> None:
        self._provider = provider

    @property
    def provider(self) -> OpenAITextProvider:
        if self._provider is None:
            self._provider = OpenAITextProvider()
        return self._provider

    def analyze_personality(self, *, cards: list[DrawnCard], arcana_name: str, profile: dict, language: str) -> str:
        return self.provider.generate(
            instructions=SYSTEM,
            input_text=f"""{output_language_instruction(language)}
Analyze the six-card sequence as the personality of one past life. Use the hidden past-life
personal arcana ({arcana_name}) and the user's MBTI ({profile.get('mbti') or 'unknown'}) only as
silent interpretive parameters; never name either one. Write no more than three short paragraphs.
Be assertive and specific. Clearly distinguish: details the spread indicates certainly happened,
events that probably happened, and experiences that did not happen because they conflict with
this personality. Avoid generic statements.

CARDS:
{self._cards(cards)}""",
        )

    def infer_theme(self, *, word: str, arcana_name: str, profile: dict, language: str) -> dict:
        schema = {
            "type": "object",
            "properties": {
                "candidates": {"type": "array", "minItems": 5, "maxItems": 5, "items": {
                    "type": "object", "properties": {
                        "theme": {"type": "string"}, "score": {"type": "integer"}, "reason": {"type": "string"}
                    }, "required": ["theme", "score", "reason"], "additionalProperties": False}},
                "selected_theme": {"type": "string"},
                "question": {"type": "string"},
            },
            "required": ["candidates", "selected_theme", "question"],
            "additionalProperties": False,
        }
        return self.provider.generate_structured(
            instructions=SYSTEM,
            schema_name="past_life_theme",
            schema=schema,
            input_text=f"""{output_language_instruction(language)}
The first word that came to the user after focused meditation about a past-life question was:
{word!r}. Generate exactly five concrete possible themes for the hidden concern. Seek a middle
semantic distance by tangency: neither a category containing the word nor a mere attribute of it,
but a theme that encounters it accidentally with meaningful frequency. Never use themes as broad
as 'family'; prefer concrete formulations such as 'unresolved recurring family cycles'. Score all
five using the profile and hidden word arcana, then select the highest. Create one natural yes/no
intuitive question about it. Do not reveal scoring or profile data in the question.

HIDDEN WORD ARCANA: {arcana_name}
PROFILE: {json.dumps(profile, ensure_ascii=False, default=str)}""",
        )

    def choose_alternate_theme(self, *, candidates: list[dict], rejected_theme: str, arcana_name: str, profile: dict, language: str) -> str:
        result = self.provider.generate_structured(
            instructions=SYSTEM,
            schema_name="alternate_past_life_theme",
            schema={"type": "object", "properties": {"selected_theme": {"type": "string"}}, "required": ["selected_theme"], "additionalProperties": False},
            input_text=f"""{output_language_instruction(language)}
The user rejected the initial inferred theme. Silently choose the best different theme, guided
primarily by the hidden word arcana and secondarily by the profile. Return only structured data.
REJECTED: {rejected_theme}
CANDIDATES: {json.dumps(candidates, ensure_ascii=False)}
HIDDEN ARCANA: {arcana_name}
PROFILE: {json.dumps(profile, ensure_ascii=False, default=str)}""",
        )
        return str(result["selected_theme"])

    def analyze_identity(self, *, cards: list[DrawnCard], word: str, arcana_name: str, theme: str, profile: dict, language: str) -> str:
        return self.provider.generate(
            instructions=SYSTEM,
            input_text=f"""{output_language_instruction(language)}
Construct a cohesive final reading about one past life. The hidden theme ({theme}) and the
word-derived arcana ({arcana_name}) are interpretive keys for every section. Never state the theme
explicitly. You may conclude that the past life's personal arcana was {arcana_name}, explaining
that this follows from the user's word and the cards.

Interpret positions exactly:
- Cards 1–2: behavior, rational/emotional tendency and temperament.
- Cards 3–4: concrete likely profession and working conditions.
- Cards 5–6: where this person lived and where/how their life ended. Give special weight to the
  visual scenery, figures, architecture, landscape, direction and elements depicted on the cards.
End with a concise synthesis answering who this person was. Be specific and assertive, while
keeping the narrative coherent rather than listing disconnected meanings.

MEDITATION WORD: {word}
HIDDEN PROFILE: {json.dumps(profile, ensure_ascii=False, default=str)}
CARDS:
{self._cards(cards)}""",
        )

    @staticmethod
    def _cards(cards: list[DrawnCard]) -> str:
        lines = []
        for item in cards:
            metadata = item.card.metadata
            knowledge = INTERPRETATION_KNOWLEDGE[item.card.code]
            lines.append(
                f"{item.position.index}. {item.card.name} ({item.orientation.value}); "
                f"visual/element: {metadata.element if metadata else None}, "
                f"astrology: {metadata.astrological_association if metadata else None}; "
                f"meaning: {knowledge.general}"
            )
        return "\n".join(lines)


past_life_ai_service = PastLifeAIService()
