from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import stripe
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.payments.config import PaymentSettings, get_payment_settings
from app.persistence.models import TarotPaymentEntity


class PaymentConfigurationError(RuntimeError):
    pass


class PaymentProviderError(RuntimeError):
    pass


SUPPORTED_PAYMENT_CURRENCIES = {"usd", "brl"}


class TarotPaymentService:
    def create_checkout_session(
        self,
        *,
        db: Session,
        user_id: int,
        conversation_id: int,
        language: str,
    ) -> TarotPaymentEntity:
        """Create the payment gate and an initial USD Stripe session.

        The WhatsApp link points to our currency-choice page. An initial Stripe
        session is created immediately so Stripe can still emit an expiration
        event if the user never opens the choice page. If BRL is selected, that
        session is replaced by a BRL session before checkout.
        """
        settings = get_payment_settings()
        if not settings.stripe_secret_key:
            raise PaymentConfigurationError("STRIPE_SECRET_KEY is not configured.")

        choice_token = secrets.token_urlsafe(24)
        expires_at = datetime.now(timezone.utc) + timedelta(
            minutes=settings.checkout_expiration_minutes
        )

        session = self._create_stripe_session(
            settings=settings,
            user_id=user_id,
            conversation_id=conversation_id,
            language=language,
            currency="usd",
            expires_at=expires_at,
        )

        choice_url = (
            f"{settings.public_base_url}/api/payments/choose/{choice_token}"
        )
        payment = TarotPaymentEntity(
            user_id=user_id,
            conversation_id=conversation_id,
            provider="stripe",
            provider_session_id=session.id,
            checkout_choice_token=choice_token,
            checkout_url=choice_url,
            amount_cents=settings.usd_amount_cents,
            currency="usd",
            status="PENDING",
            expires_at=expires_at,
        )
        db.add(payment)
        db.commit()
        db.refresh(payment)
        return payment

    def choose_currency(
        self,
        *,
        db: Session,
        choice_token: str,
        currency: str,
        language: str,
    ) -> TarotPaymentEntity:
        normalized = currency.strip().lower()
        if normalized not in SUPPORTED_PAYMENT_CURRENCIES:
            raise ValueError("Unsupported payment currency.")

        payment = self.get_by_choice_token(db, choice_token)
        if payment is None:
            raise ValueError("Payment not found.")
        if payment.status != "PENDING":
            raise ValueError("Payment is no longer pending.")

        settings = get_payment_settings()
        if not settings.stripe_secret_key:
            raise PaymentConfigurationError("STRIPE_SECRET_KEY is not configured.")
        stripe.api_key = settings.stripe_secret_key

        now = datetime.now(timezone.utc)
        if payment.expires_at is not None and payment.expires_at <= now:
            payment.status = "EXPIRED"
            db.commit()
            raise ValueError("Payment has expired.")

        # If this currency already owns the current Stripe session, retrieve its
        # Checkout URL instead of creating a duplicate session.
        if payment.currency == normalized:
            try:
                session = stripe.checkout.Session.retrieve(payment.provider_session_id)
            except Exception as exc:
                raise PaymentProviderError(
                    f"Unable to retrieve Stripe Checkout session: {exc}"
                ) from exc

            session_url = getattr(session, "url", None)
            session_status = getattr(session, "status", None)
            if session_url and session_status == "open":
                payment.checkout_url = session_url
                db.commit()
                db.refresh(payment)
                return payment

        expires_at = now + timedelta(minutes=settings.checkout_expiration_minutes)
        old_session_id = payment.provider_session_id
        session = self._create_stripe_session(
            settings=settings,
            user_id=payment.user_id,
            conversation_id=payment.conversation_id,
            language=language,
            currency=normalized,
            expires_at=expires_at,
        )

        payment.provider_session_id = session.id
        payment.checkout_url = session.url
        payment.currency = normalized
        payment.amount_cents = settings.amount_for_currency(normalized)
        payment.expires_at = expires_at
        db.commit()
        db.refresh(payment)

        if old_session_id and old_session_id != session.id:
            try:
                stripe.checkout.Session.expire(old_session_id)
            except Exception:
                # The new session is already persisted and is now the source of
                # truth. Failure to expire the old unused session must not block
                # the customer's checkout.
                pass

        return payment

    def get_by_choice_token(
        self,
        db: Session,
        choice_token: str,
    ) -> TarotPaymentEntity | None:
        return db.scalar(
            select(TarotPaymentEntity).where(
                TarotPaymentEntity.checkout_choice_token == choice_token
            )
        )

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
                # The local state still cancels the WhatsApp flow if Stripe is
                # temporarily unreachable.
                pass

        payment.status = "CANCELLED"
        db.commit()

    @staticmethod
    def _create_stripe_session(
        *,
        settings: PaymentSettings,
        user_id: int,
        conversation_id: int,
        language: str,
        currency: str,
        expires_at: datetime,
    ):
        stripe.api_key = settings.stripe_secret_key
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
                            "currency": currency,
                            "unit_amount": settings.amount_for_currency(currency),
                            "product_data": {"name": product_name},
                        },
                        "quantity": 1,
                    }
                ],
                metadata={
                    "user_id": str(user_id),
                    "conversation_id": str(conversation_id),
                    "purpose": "tarot_reading",
                    "currency": currency,
                },
                success_url=(
                    f"{settings.public_base_url}/api/payments/success"
                    "?session_id={CHECKOUT_SESSION_ID}"
                ),
                cancel_url=f"{settings.public_base_url}/api/payments/cancelled",
                expires_at=int(expires_at.timestamp()),
            )
        except Exception as exc:
            raise PaymentProviderError(
                f"Unable to create Stripe Checkout session: {exc}"
            ) from exc

        if not getattr(session, "url", None):
            raise PaymentProviderError("Stripe did not return a Checkout URL.")
        return session


tarot_payment_service = TarotPaymentService()
