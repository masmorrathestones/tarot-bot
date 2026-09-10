import os
from dataclasses import dataclass


@dataclass(frozen=True)
class XSettings:
    api_key: str | None
    api_secret: str | None
    access_token: str | None
    access_token_secret: str | None
    admin_token: str | None
    api_base_url: str = "https://api.x.com"
    scheduler_enabled: bool = True
    scheduler_interval_seconds: int = 30

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


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def get_x_settings() -> XSettings:
    return XSettings(
        api_key=os.getenv("X_API_KEY") or None,
        api_secret=os.getenv("X_API_SECRET") or None,
        access_token=os.getenv("X_ACCESS_TOKEN") or None,
        access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET") or None,
        admin_token=os.getenv("X_SCHEDULER_ADMIN_TOKEN") or None,
        api_base_url=(os.getenv("X_API_BASE_URL") or "https://api.x.com").rstrip("/"),
        scheduler_enabled=_env_bool("X_SCHEDULER_ENABLED", True),
        scheduler_interval_seconds=max(
            15,
            int(os.getenv("X_SCHEDULER_INTERVAL_SECONDS", "30")),
        ),
    )
