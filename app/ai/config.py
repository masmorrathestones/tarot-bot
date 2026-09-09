import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class AISettings:
    api_key: str | None
    model: str


def get_ai_settings() -> AISettings:
    return AISettings(
        api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL", "gpt-5.6-luna"),
    )
