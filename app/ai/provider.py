import json
from typing import Any

from openai import OpenAI

from app.ai.config import get_ai_settings


class AIConfigurationError(RuntimeError):
    pass


class AIProviderError(RuntimeError):
    pass


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
                instructions=instructions,
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
        """Generate JSON that must match the supplied JSON Schema.

        The Responses API Structured Outputs mode is used with strict schema
        adherence. The caller still validates the parsed value against its
        application-level allow-list before using it.
        """
        try:
            response = self.client.responses.create(
                model=self.model,
                instructions=instructions,
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
            raise AIProviderError(
                f"AI structured provider request failed: {exc}"
            ) from exc
