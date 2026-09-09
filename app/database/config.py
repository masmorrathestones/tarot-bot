import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class DatabaseSettings:
    url: str


def get_database_settings() -> DatabaseSettings:
    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Create a .env file from .env.example and configure PostgreSQL."
        )
    return DatabaseSettings(url=url)
