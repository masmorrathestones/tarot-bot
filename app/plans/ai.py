from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.ai.provider import OpenAITextProvider
from app.tarot.enums import Orientation
from app.tarot.interpretation_knowledge import INTERPRETATION_KNOWLEDGE
from app.tarot.models import TarotCard
from app.tarot.mystic_intuition import MYSTIC_INTUITION_DESCRIPTIONS


class PlanAnalysisService:
    def __init__(self, provider: OpenAITextProvider | None = None) -> None:
        self._provider = provider

    @property
    def provider(self) -> OpenAITextProvider:
        if self._provider is None:
            self._provider = OpenAITextProvider()
        return self._provider

    def daily_card_analysis(
        self,
        *,
        card: TarotCard,
        orientation: Orientation,
        language: str,
        personal_arcana: str | None,
        year_arcana: str | None,
        mbti: str | None,
        intuition_alignment: str,
        intuition_weight: int,
    ) -> str:
        metadata = card.metadata
        knowledge = INTERPRETATION_KNOWLEDGE[card.code]
        if orientation == Orientation.REVERSED:
            orientation_meaning = metadata.reversed_meaning if metadata else knowledge.general
            keywords = list(metadata.reversed_keywords) if metadata else []
        else:
            orientation_meaning = metadata.upright_meaning if metadata else knowledge.general
            keywords = list(metadata.upright_keywords) if metadata else []

        instruction = MYSTIC_INTUITION_DESCRIPTIONS[intuition_alignment]
        language_name = {"pt": "Brazilian Portuguese", "es": "Spanish"}.get(language, "English")

        system = (
            "You write a concise daily one-card Tarot guidance message. The card is primary evidence. "
            "Use the Personal Arcana, Year Arcana and MBTI only as secondary personalization. Never explicitly mention MBTI labels. "
            "Give practical advice, cautions, opportunities and suggestions for the user's day. Be directional and useful rather than vague. "
            "Do not claim guaranteed future facts. Do not reveal the mystic intuition alignment, weight, randomization or internal mechanism. "
            "The hidden intuition must influence the reading proportionally to its weight; weight 0 has effectively no influence, 1-3 subtle, 4-7 moderate, 8-10 strong. "
            "When weight is 9 or 10, treat it as dominant interpretive pressure unless the card clearly contradicts it. "
            f"Write entirely in {language_name}."
        )
        prompt = {
            "card": card.name,
            "orientation": orientation.value,
            "keywords": keywords,
            "orientation_meaning": orientation_meaning,
            "source_interpretation": knowledge.general,
            "personal_arcana": personal_arcana,
            "year_arcana": year_arcana,
            "mbti_internal_only": mbti,
            "hidden_intuition": {
                "interpretive_instruction": instruction,
                "weight_0_to_10": intuition_weight,
            },
            "task": (
                "Produce a compact daily reading. Start with the main message of the card for today. "
                "Then give concrete advice and warnings, plus 2-4 useful suggestions for how to use the day well. "
                "Do not include headings about internal systems or the hidden intuition."
            ),
        }
        return self.provider.generate(instructions=system, input_text=json.dumps(prompt, ensure_ascii=False, default=str))

    def weekly_astrology_analysis(
        self,
        *,
        natal_chart: dict[str, Any],
        current_place: str,
        current_timezone: str,
        weekly_transits: dict[str, Any],
        language: str,
        generated_at: datetime,
    ) -> str:
        language_name = {"pt": "Brazilian Portuguese", "es": "Spanish"}.get(language, "English")
        system = (
            "You write a weekly astrology forecast by interpreting deterministic natal-chart and transit data supplied by the application. "
            "Do not calculate or invent planetary positions: use only the supplied chart and transits. "
            "Give a broad diagnosis of the week's symbolic tendencies: challenges, opportunities, discoveries, relationships, work, energy, decisions and practical timing. "
            "Provide specific day-by-day guidance when the transit data supports it, including ordinary lifestyle suggestions such as which days may be better for social plans, study, difficult conversations, rest, grooming or getting a haircut. "
            "Do not give medical, legal or financial instructions from astrology. Do not present events as guaranteed facts. "
            "However, avoid generic hedging: identify the strongest tendencies and state them clearly. "
            f"Write entirely in {language_name}."
        )
        prompt = {
            "generated_at": generated_at.isoformat(),
            "current_place": current_place,
            "current_timezone": current_timezone,
            "natal_chart": natal_chart,
            "weekly_transits": weekly_transits,
            "task": (
                "Produce a detailed forecast for the next seven days. Begin with the week's overall tone, then discuss the most important themes and challenges, "
                "then give a day-by-day section with practical advice and favorable/cautionary windows, and close with the most important guidance for the week."
            ),
        }
        return self.provider.generate(instructions=system, input_text=json.dumps(prompt, ensure_ascii=False, default=str))


plan_analysis_service = PlanAnalysisService()
