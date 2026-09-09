import json
from typing import Any

from openai import OpenAI

from app.ai.config import get_ai_settings


class AIConfigurationError(RuntimeError):
    pass


class AIProviderError(RuntimeError):
    pass


def _with_language_requirement(instructions: str, input_text: str) -> str:
    """Promote an explicit reading language requirement to instruction level."""
    for line in input_text.splitlines():
        if line.startswith("LANGUAGE REQUIREMENT:"):
            cleaned = instructions.replace(
                "All generated reading content must be in English.",
                "Follow the LANGUAGE REQUIREMENT appended below for all user-facing reading content.",
            ).replace(
                "Write in English.",
                "Follow the LANGUAGE REQUIREMENT appended below.",
            )
            return f"{cleaned}\n\n{line}"
    return instructions


class OpenAITextProvider:
    def __init__(self) -> None:
        settings = get_ai_settings()

        if not settings.api_key:
            raise AIConfigurationError(
                "OPENAI_API_KEY is not configured. "
                "Create a .env file from .env.example and add your API key."
            )

        self.model = settings.model
        self.client = OpenAI(api_key=settings.api_key)

    def generate(self, *, instructions: str, input_text: str) -> str:
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=_with_language_requirement(instructions, input_text),
                input=input_text,
            )
            return response.output_text.strip()
        except Exception as exc:
            raise AIProviderError(f"AI provider request failed: {exc}") from exc

    def generate_structured(
        self,
        *,
        instructions: str,
        input_text: str,
        schema_name: str,
        schema: dict[str, Any],
    ) -> dict[str, Any]:
        """Generate JSON that must match the supplied JSON Schema."""
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=_with_language_requirement(instructions, input_text),
                input=input_text,
                text={
                    "format": {
                        "type": "json_schema",
                        "name": schema_name,
                        "schema": schema,
                        "strict": True,
                    }
                },
            )
            payload = json.loads(response.output_text)
            if not isinstance(payload, dict):
                raise ValueError("Structured response was not a JSON object.")
            return payload
        except AIProviderError:
            raise
        except Exception as exc:
            raise AIProviderError(f"AI structured provider request failed: {exc}") from exc
