import json
from typing import Any

from openai import OpenAI

from app.ai.config import get_ai_settings


class AIConfigurationError(RuntimeError):
    pass


class AIProviderError(RuntimeError):
    pass


def _prepare_language_request(instructions: str, input_text: str) -> tuple[str, str]:
    """Make the selected WhatsApp reading language authoritative.

    Existing Tarot prompts were originally written as English-only tasks. When
    a LANGUAGE REQUIREMENT is present in the reading context, remove those
    legacy output-language directives from both instruction and input layers,
    then promote the selected language to the provider instruction layer.
    """
    language_requirement = next(
        (
            line
            for line in input_text.splitlines()
            if line.startswith("LANGUAGE REQUIREMENT:")
        ),
        None,
    )
    if language_requirement is None:
        return instructions, input_text

    replacements = (
        (
            "All generated reading content must be in English.",
            "Follow the LANGUAGE REQUIREMENT below for all user-facing reading content.",
        ),
        (
            "Write in English.",
            "Follow the LANGUAGE REQUIREMENT below.",
        ),
    )

    effective_instructions = instructions
    effective_input = input_text
    for old, new in replacements:
        effective_instructions = effective_instructions.replace(old, new)
        effective_input = effective_input.replace(old, new)

    effective_instructions = (
        f"{effective_instructions}\n\n{language_requirement}"
    )
    return effective_instructions, effective_input


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
            effective_instructions, effective_input = _prepare_language_request(
                instructions,
                input_text,
            )
            response = self.client.responses.create(
                model=self.model,
                instructions=effective_instructions,
                input=effective_input,
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
            effective_instructions, effective_input = _prepare_language_request(
                instructions,
                input_text,
            )
            response = self.client.responses.create(
                model=self.model,
                instructions=effective_instructions,
                input=effective_input,
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
