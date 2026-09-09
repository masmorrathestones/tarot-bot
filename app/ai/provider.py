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
