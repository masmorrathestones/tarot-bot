import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PlanSettings:
    recurring_usd_cents: int = 1000
    recurring_brl_cents: int = 6000
    one_time_usd_cents: int = 1100
    one_time_brl_cents: int = 6600
    scheduler_enabled: bool = True
    scheduler_interval_seconds: int = 60

    def amount(self, *, billing_type: str, currency: str) -> int:
        billing = billing_type.strip().lower()
        curr = currency.strip().lower()
        values = {
            ("recurring", "usd"): self.recurring_usd_cents,
            ("recurring", "brl"): self.recurring_brl_cents,
            ("one_time", "usd"): self.one_time_usd_cents,
            ("one_time", "brl"): self.one_time_brl_cents,
        }
        try:
            return values[(billing, curr)]
        except KeyError as exc:
            raise ValueError("Unsupported plan billing type or currency.") from exc


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() not in {"0", "false", "no", "off"}


def get_plan_settings() -> PlanSettings:
    return PlanSettings(
        recurring_usd_cents=int(os.getenv("PLAN_RECURRING_USD_CENTS", "1000")),
        recurring_brl_cents=int(os.getenv("PLAN_RECURRING_BRL_CENTS", "6000")),
        one_time_usd_cents=int(os.getenv("PLAN_ONE_TIME_USD_CENTS", "1100")),
        one_time_brl_cents=int(os.getenv("PLAN_ONE_TIME_BRL_CENTS", "6600")),
        scheduler_enabled=_env_bool("PLAN_SCHEDULER_ENABLED", True),
        scheduler_interval_seconds=max(30, int(os.getenv("PLAN_SCHEDULER_INTERVAL_SECONDS", "60"))),
    )
