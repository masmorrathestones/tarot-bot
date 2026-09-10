from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.ai.provider import OpenAITextProvider
from app.whatsapp.i18n import output_language_instruction


PROFILE_ANALYSIS_INSTRUCTIONS = """You create a reflective annual symbolic profile analysis from user-provided profile data.

Treat astrology, MBTI, zodiac and Tarot arcana as symbolic/self-reflection frameworks, not scientific diagnoses or deterministic prediction systems. Integrate the available information coherently instead of listing each field independently.

The full analysis should explain:
- general personality patterns and recurring tendencies;
- strengths and qualities worth consciously exploring;
- weaknesses, blind spots or habits worth correcting;
- themes, opportunities and tensions that may deserve attention during the profile's reference year;
- practical areas of attention for relationships, work/study, decisions and personal development when supported by the supplied profile.

Do not invent facts that are absent from the profile. Do not diagnose mental or physical health conditions. Do not give medical, legal or financial instructions. Do not claim certainty about future events. Phrase the annual outlook as tendencies, themes and possibilities.

Also produce a concise profile summary with 4 to 8 lines. Across those lines, cover general characteristics, qualities, weaknesses/defects to work on, and important points of attention. Each summary item must be a single concise line and useful as context for future Tarot readings.
"""


@dataclass(frozen=True)
class ProfileAnalysisResult:
    analysis: str
    summary: str


class ProfileAnalysisService:
    def __init__(self, provider: OpenAITextProvider | None = None) -> None:
        self._provider = provider

    @property
    def provider(self) -> OpenAITextProvider:
        if self._provider is None:
            self._provider = OpenAITextProvider()
        return self._provider

    def analyze(self, *, user: Any, language: str) -> ProfileAnalysisResult:
        profile = user.profile
        if profile is None:
            raise ValueError("User profile is unavailable.")

        profile_text = self._profile_text(user)
        language_requirement = output_language_instruction(language)
        reference_year = profile.year_arcana_reference_year

        payload = self.provider.generate_structured(
            instructions=PROFILE_ANALYSIS_INSTRUCTIONS,
            input_text=(
                f"{language_requirement}\n\n"
                f"REFERENCE YEAR: {reference_year or 'Not available'}\n\n"
                "USER PROFILE:\n"
                f"{profile_text}\n\n"
                "Return the full integrated annual profile analysis and a separate summary_lines array. "
                "The summary must contain between 4 and 8 concise lines."
            ),
            schema_name="profile_analysis",
            schema={
                "type": "object",
                "properties": {
                    "analysis": {"type": "string", "minLength": 1},
                    "summary_lines": {
                        "type": "array",
                        "minItems": 4,
                        "maxItems": 8,
                        "items": {"type": "string", "minLength": 1},
                    },
                },
                "required": ["analysis", "summary_lines"],
                "additionalProperties": False,
            },
        )

        analysis = str(payload.get("analysis") or "").strip()
        raw_lines = payload.get("summary_lines") or []
        summary_lines = [
            str(line).strip()
            for line in raw_lines[:8]
            if str(line).strip()
        ]
        if not analysis or not summary_lines:
            raise ValueError("AI returned an incomplete profile analysis.")

        summary = "\n".join(f"• {line}" for line in summary_lines)
        return ProfileAnalysisResult(analysis=analysis, summary=summary)

    @staticmethod
    def _profile_text(user: Any) -> str:
        p = user.profile
        data = {
            "name": user.name,
            "birth_date": p.birth_date.isoformat() if p.birth_date else None,
            "birth_time": p.birth_time.isoformat() if p.birth_time else None,
            "birth_place": p.birth_place,
            "birth_latitude": p.birth_latitude,
            "birth_longitude": p.birth_longitude,
            "birth_timezone": p.birth_timezone,
            "zodiac_sign": p.zodiac_sign,
            "sun_sign": p.sun_sign,
            "moon_sign": p.moon_sign,
            "rising_sign": p.rising_sign,
            "mbti": p.mbti,
            "personal_number": p.personal_number,
            "personal_arcana_number": p.personal_arcana_number,
            "personal_arcana_name": p.personal_arcana_name,
            "year_arcana_number": p.year_arcana_number,
            "year_arcana_name": p.year_arcana_name,
            "year_arcana_reference_year": p.year_arcana_reference_year,
            "natal_chart": p.natal_chart,
        }
        return "\n".join(
            f"{key}: {value}"
            for key, value in data.items()
            if value is not None and value != "" and value != {} and value != []
        )


profile_analysis_service = ProfileAnalysisService()
