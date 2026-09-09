import json
from typing import Any

from app.ai.provider import AIProviderError, OpenAITextProvider
from app.tarot.spreads import SPREADS


class SpreadSelectionError(RuntimeError):
    pass


class SpreadSelectionService:
    def __init__(self, provider: OpenAITextProvider | None = None) -> None:
        self._provider = provider

    @property
    def provider(self) -> OpenAITextProvider:
        if self._provider is None:
            self._provider = OpenAITextProvider()
        return self._provider

    def choose_spread(
        self,
        *,
        question: str,
        context: str | None,
        profile_snapshot: dict[str, Any] | None,
    ) -> str:
        available_codes = list(SPREADS.keys())
        if not available_codes:
            raise SpreadSelectionError("No Tarot spreads are configured.")

        catalog = []
        for spread in SPREADS.values():
            catalog.append(
                {
                    "code": spread.code,
                    "name": spread.name,
                    "description": spread.description,
                    "card_count": len(spread.positions),
                    "positions": [
                        {
                            "index": position.index,
                            "name": position.name,
                            "description": position.description,
                        }
                        for position in spread.positions
                    ],
                }
            )

        profile = {
            key: value
            for key, value in (profile_snapshot or {}).items()
            if key != "whatsapp_number"
            and value is not None
            and value != ""
            and value != {}
            and value != []
        }

        schema = {
            "type": "object",
            "properties": {
                "spread_code": {
                    "type": "string",
                    "enum": available_codes,
                }
            },
            "required": ["spread_code"],
            "additionalProperties": False,
        }

        instructions = (
            "You select the most appropriate Tarot spread for a reading. "
            "Choose exactly one of the provided spread codes based on the user's "
            "question, additional context, and available personal profile. "
            "The profile is secondary context: do not choose a spread merely to "
            "confirm astrology, MBTI, numerology, or a desired outcome. "
            "Do not invent a spread and do not return commentary."
        )

        input_text = (
            "USER QUESTION:\n"
            f"{question}\n\n"
            "ADDITIONAL CONTEXT:\n"
            f"{context or 'None provided'}\n\n"
            "POPULATED USER PROFILE:\n"
            f"{json.dumps(profile, ensure_ascii=False, default=str, indent=2)}\n\n"
            "AVAILABLE SPREADS:\n"
            f"{json.dumps(catalog, ensure_ascii=False, indent=2)}"
        )

        try:
            result = self.provider.generate_structured(
                instructions=instructions,
                input_text=input_text,
                schema_name="tarot_spread_selection",
                schema=schema,
            )
        except AIProviderError:
            raise

        spread_code = result.get("spread_code")
        if spread_code not in SPREADS:
            raise SpreadSelectionError(
                "The AI returned a spread outside the configured allow-list."
            )
        return str(spread_code)


spread_selection_service = SpreadSelectionService()
