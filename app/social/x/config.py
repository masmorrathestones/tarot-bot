import os
from dataclasses import dataclass


DEFAULT_PROSPECT_QUERIES = (
    '("tarot" OR "tarô") ("alguém" OR "indica" OR "leitura" OR "tiragem") lang:pt -is:retweet -from:holomancytarot',
    '("tarot reading" OR "tarot reader") ("need" OR "looking" OR "recommend" OR "anyone") lang:en -is:retweet -from:holomancytarot',
    '("tarot" OR "lectura de tarot") ("busco" OR "recomienda" OR "alguien" OR "lectura") lang:es -is:retweet -from:holomancytarot',
)


@dataclass(frozen=True)
class XSettings:
    api_key: str | None
    api_secret: str | None
    access_token: str | None
    access_token_secret: str | None
    bearer_token: str | None
    admin_token: str | None
    api_base_url: str = "https://api.x.com"
    scheduler_enabled: bool = True
    scheduler_interval_seconds: int = 30
    prospecting_enabled: bool = True
    prospecting_interval_seconds: int = 7200
    prospecting_min_score: int = 5
    prospecting_max_per_run: int = 5
    prospect_queries: tuple[str, ...] = DEFAULT_PROSPECT_QUERIES

    @property
    def posting_configured(self) -> bool:
        return all(
            (
                self.api_key,
                self.api_secret,
                self.access_token,
                self.access_token_secret,
            )
        )

    @property
    def search_configured(self) -> bool:
        return bool(self.bearer_token)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def _prospect_queries() -> tuple[str, ...]:
    raw = (os.getenv("X_PROSPECT_QUERIES") or "").strip()
    if not raw:
        return DEFAULT_PROSPECT_QUERIES
    queries = tuple(query.strip() for query in raw.split("||") if query.strip())
    return queries or DEFAULT_PROSPECT_QUERIES


def get_x_settings() -> XSettings:
    return XSettings(
        api_key=os.getenv("X_API_KEY") or None,
        api_secret=os.getenv("X_API_SECRET") or None,
        access_token=os.getenv("X_ACCESS_TOKEN") or None,
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET") or None,
        bearer_token=os.getenv("X_BEARER_TOKEN") or None,
        admin_token=os.getenv("X_SCHEDULER_ADMIN_TOKEN") or None,
        api_base_url=(os.getenv("X_API_BASE_URL") or "https://api.x.com").rstrip("/"),
        scheduler_enabled=_env_bool("X_SCHEDULER_ENABLED", True),
        scheduler_interval_seconds=max(
            15,
            int(os.getenv("X_SCHEDULER_INTERVAL_SECONDS", "30")),
        ),
        prospecting_enabled=_env_bool("X_PROSPECTING_ENABLED", True),
        prospecting_interval_seconds=max(
            3600,
            int(os.getenv("X_PROSPECTING_INTERVAL_SECONDS", "7200")),
        ),
        prospecting_min_score=max(
            1,
            int(os.getenv("X_PROSPECTING_MIN_SCORE", "5")),
        ),
        prospecting_max_per_run=max(
            1,
            min(20, int(os.getenv("X_PROSPECTING_MAX_PER_RUN", "5"))),
        ),
        prospect_queries=_prospect_queries(),
    )
