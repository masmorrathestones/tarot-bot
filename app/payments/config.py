import os
from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentSettings:
    stripe_secret_key: str
    stripe_webhook_secret: str
    public_base_url: str
    amount_cents: int = 100
    currency: str = "usd"
    checkout_expiration_minutes: int = 31


def get_payment_settings() -> PaymentSettings:
    return PaymentSettings(
        stripe_secret_key=os.getenv("STRIPE_SECRET_KEY", "").strip(),
        stripe_webhook_secret=os.getenv("STRIPE_WEBHOOK_SECRET", "").strip(),
        public_base_url=os.getenv(
            "PUBLIC_BASE_URL",
            "https://tarot-bot-c1fv.onrender.com",
        ).rstrip("/"),
    )
