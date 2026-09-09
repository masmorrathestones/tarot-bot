from __future__ import annotations

from datetime import datetime, timedelta, timezone

import stripe
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.payments.config import get_payment_settings
from app.persistence.models import TarotPaymentEntity


class PaymentConfigurationError(RuntimeError):
    pass


class PaymentProviderError(RuntimeError):
    pass


class TarotPaymentService:
    def create_checkout_session(
        self,
        *,
        db: Session,
        user_id: int,
        conversation_id: int,
        language: str,
    ) -> TarotPaymentEntity:
        settings = get_payment_settings()
        if not settings.stripe_secret_key:
            raise PaymentConfigurationError("STRIPE_SECRET_KEY is not configured.")

        stripe.api_key = settings.stripe_secret_key
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.checkout_expiration_minutes
        )

        product_name = {
            "pt": "Leitura de Tarô",
            "es": "Lectura de Tarot",
        }.get(language, "Tarot reading")

        try:
            session = stripe.checkout.Session.create(
                mode="payment",
                payment_method_types=["card"],
                line_items=[
                    {
                        "price_data": {
                            "currency": settings.currency,
                            "unit_amount": settings.amount_cents,
                            "product_data": {"name": product_name},
                        },
                        "quantity": 1,
                    }
                ],
                metadata={
                    "user_id": str(user_id),
                    "conversation_id": str(conversation_id),
                    "purpose": "tarot_reading",
                },
                success_url=(
                    f"{settings.public_base_url}/api/payments/success"
                    "?session_id={CHECKOUT_SESSION_ID}"
                ),
                cancel_url=f"{settings.public_base_url}/api/payments/cancelled",
                expires_at=int(expires_at.timestamp()),
            )
        except Exception as exc:
            raise PaymentProviderError(f"Unable to create Stripe Checkout session: {exc}") from exc

        if not session.url:
            raise PaymentProviderError("Stripe did not return a Checkout URL.")

        payment = TarotPaymentEntity(
            user_id=user_id,
            conversation_id=conversation_id,
            provider="stripe",
            provider_session_id=session.id,
            checkout_url=session.url,
            amount_cents=settings.amount_cents,
            currency=settings.currency,
            status="PENDING",
            expires_at=expires_at,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    def get_by_session_id(
        self,
        db: Session,
        provider_session_id: str,
    ) -> TarotPaymentEntity | None:
        return db.scalar(
            select(TarotPaymentEntity).where(
                TarotPaymentEntity.provider_session_id == provider_session_id
            )
        )

    def mark_paid(
        self,
        *,
        db: Session,
        provider_session_id: str,
    ) -> tuple[TarotPaymentEntity | None, bool]:
        payment = self.get_by_session_id(db, provider_session_id)
        if payment is None:
            return None, False
        if payment.status == "PAID":
            return payment, False
        if payment.status in {"EXPIRED", "CANCELLED"}:
            return payment, False

        payment.status = "PAID"
        payment.paid_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(payment)
        return payment, True

    def mark_expired(
        self,
        *,
        db: Session,
        provider_session_id: str,
    ) -> tuple[TarotPaymentEntity | None, bool]:
        payment = self.get_by_session_id(db, provider_session_id)
        if payment is None:
            return None, False
        if payment.status != "PENDING":
            return payment, False

        payment.status = "EXPIRED"
        db.commit()
        db.refresh(payment)
        return payment, True

    def cancel_pending_for_conversation(
        self,
        *,
        db: Session,
        conversation_id: int,
    ) -> None:
        payment = db.scalar(
            select(TarotPaymentEntity)
            .where(
                TarotPaymentEntity.conversation_id == conversation_id,
                TarotPaymentEntity.status == "PENDING",
            )
            .order_by(TarotPaymentEntity.id.desc())
            .limit(1)
        )
        if payment is None:
            return

        settings = get_payment_settings()
        if settings.stripe_secret_key:
            stripe.api_key = settings.stripe_secret_key
            try:
                stripe.checkout.Session.expire(payment.provider_session_id)
            except Exception:
                # The webhook/payment state remains the source of truth; cancellation
                # should still return the WhatsApp flow to the menu even if Stripe
                # cannot be reached at this moment.
                pass

        payment.status = "CANCELLED"
        db.commit()


tarot_payment_service = TarotPaymentService()
