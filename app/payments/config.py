import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentSettings:
    stripe_secret_key: str
    stripe_webhook_secret: str
    public_base_url: str
    usd_amount_cents: int = 100
    brl_amount_cents: int = 600
    checkout_expiration_minutes: int = 31

    def amount_for_currency(self, currency: str) -> int:
        normalized = currency.strip().lower()
        if normalized == "usd":
            return self.usd_amount_cents
        if normalized == "brl":
            return self.brl_amount_cents
        raise ValueError(f"Unsupported payment currency: {currency}")


def get_payment_settings() -> PaymentSettings:
    return PaymentSettings(
        stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", "").strip(),
        stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", "").strip(),
        public_base_url=os.getenv(
            "PUBLIC_BASE_URL",
            "https://tarot-bot-c1fv.onrender.com",
        ).rstrip("/"),
        usd_amount_cents=int(os.getenv("TAROT_PRICE_USD_CENTS", "100")),
        brl_amount_cents=int(os.getenv("TAROT_PRICE_BRL_CENTS", "600")),
    )
