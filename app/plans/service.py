from __future__ import annotations

import secrets
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import stripe
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.payments.config import get_payment_settings
from app.plans.config import get_plan_settings
from app.plans.models import DailyWeeklyPlanEntity


ACTIVE_PLAN_STATUSES = {"ACTIVE", "CANCEL_AT_PERIOD_END"}
WEEKDAY_NAMES = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


class PlanConfigurationError(RuntimeError):
    pass


class PlanProviderError(RuntimeError):
    pass


class DailyWeeklyPlanService:
    def get_for_user(self, db: Session, user_id: int) -> DailyWeeklyPlanEntity | None:
        return db.scalar(select(DailyWeeklyPlanEntity).where(DailyWeeklyPlanEntity.user_id == user_id))

    def get_or_create_draft(self, db: Session, user_id: int) -> DailyWeeklyPlanEntity:
        plan = self.get_for_user(db, user_id)
        if plan is None:
            plan = DailyWeeklyPlanEntity(user_id=user_id, status="DRAFT")
            db.add(plan)
            db.commit()
            db.refresh(plan)
        elif plan.status in {"EXPIRED", "CANCELLED"}:
            plan.status = "DRAFT"
            plan.billing_type = None
            plan.currency = None
            plan.amount_cents = None
            plan.checkout_token = None
            plan.stripe_checkout_session_id = None
            plan.stripe_customer_id = None
            plan.stripe_subscription_id = None
            plan.starts_at = None
            plan.current_period_end = None
            plan.cancel_at_period_end = False
            plan.next_daily_at = None
            plan.next_weekly_at = None
            db.commit()
            db.refresh(plan)
        return plan

    def is_active(self, plan: DailyWeeklyPlanEntity | None, now: datetime | None = None) -> bool:
        if plan is None or plan.status not in ACTIVE_PLAN_STATUSES:
            return False
        current = now or datetime.now(timezone.utc)
        return plan.current_period_end is None or plan.current_period_end > current

    def profile_location(self, db: Session, user_id: int) -> dict | None:
        row = db.execute(
            text(
                "SELECT current_place, current_latitude, current_longitude, current_timezone, current_location_updated_at "
                "FROM user_profiles WHERE user_id = :user_id"
            ),
            {"user_id": user_id},
        ).mappings().first()
        if not row or not row.get("current_place") or not row.get("current_timezone"):
            return None
        return dict(row)

    def save_current_location(
        self,
        *,
        db: Session,
        user_id: int,
        place: str,
        latitude: float,
        longitude: float,
        timezone_name: str,
    ) -> None:
        db.execute(
            text(
                "UPDATE user_profiles SET current_place=:place, current_latitude=:lat, current_longitude=:lon, "
                "current_timezone=:tz, current_location_updated_at=:updated_at WHERE user_id=:user_id"
            ),
            {
                "place": place[:250],
                "lat": latitude,
                "lon": longitude,
                "tz": timezone_name,
                "updated_at": datetime.now(timezone.utc),
                "user_id": user_id,
            },
        )
        plan = self.get_for_user(db, user_id)
        if plan and self.is_active(plan):
            plan.schedule_timezone = timezone_name
            plan.next_daily_at = self.next_daily_occurrence(
                daily_time=plan.daily_time,
                timezone_name=timezone_name,
                last_sent_at=plan.last_daily_sent_at,
            )
            plan.next_weekly_at = self.next_weekly_occurrence(
                weekday=plan.weekly_weekday,
                weekly_time=plan.weekly_time,
                timezone_name=timezone_name,
                last_sent_at=plan.last_weekly_sent_at,
            )
        db.commit()

    def configure_daily_time(self, db: Session, plan: DailyWeeklyPlanEntity, value: time) -> None:
        plan.daily_time = value
        if self.is_active(plan) and plan.schedule_timezone:
            plan.next_daily_at = self.next_daily_occurrence(
                daily_time=value,
                timezone_name=plan.schedule_timezone,
                last_sent_at=plan.last_daily_sent_at,
            )
        db.commit()

    def configure_weekly(self, db: Session, plan: DailyWeeklyPlanEntity, weekday: int, value: time) -> None:
        if not 0 <= weekday <= 6:
            raise ValueError("Weekday must be between 0 and 6.")
        plan.weekly_weekday = weekday
        plan.weekly_time = value
        if self.is_active(plan) and plan.schedule_timezone:
            plan.next_weekly_at = self.next_weekly_occurrence(
                weekday=weekday,
                weekly_time=value,
                timezone_name=plan.schedule_timezone,
                last_sent_at=plan.last_weekly_sent_at,
            )
        db.commit()

    def prepare_checkout(self, *, db: Session, plan: DailyWeeklyPlanEntity, billing_type: str) -> str:
        if billing_type not in {"recurring", "one_time"}:
            raise ValueError("Unsupported billing type.")
        if plan.daily_time is None or plan.weekly_weekday is None or plan.weekly_time is None:
            raise ValueError("Plan schedule is incomplete.")
        location = self.profile_location(db, plan.user_id)
        if location is None:
            raise ValueError("Current location is required before checkout.")
        token = secrets.token_urlsafe(32)
        plan.billing_type = billing_type
        plan.checkout_token = token
        plan.status = "AWAITING_PAYMENT"
        plan.schedule_timezone = str(location["current_timezone"])
        db.commit()
        base_url = get_payment_settings().public_base_url
        return f"{base_url}/api/plans/checkout/{token}"

    def get_by_checkout_token(self, db: Session, token: str) -> DailyWeeklyPlanEntity | None:
        return db.scalar(select(DailyWeeklyPlanEntity).where(DailyWeeklyPlanEntity.checkout_token == token))

    def start_checkout(self, *, db: Session, plan: DailyWeeklyPlanEntity, currency: str, language: str) -> str:
        currency = currency.lower().strip()
        if currency not in {"usd", "brl"}:
            raise ValueError("Unsupported currency.")
        if plan.status != "AWAITING_PAYMENT" or plan.billing_type not in {"recurring", "one_time"}:
            raise ValueError("Plan is not ready for payment.")

        payment_settings = get_payment_settings()
        if not payment_settings.stripe_secret_key:
            raise PlanConfigurationError("STRIPE_SECRET_KEY is not configured.")
        stripe.api_key = payment_settings.stripe_secret_key
        amount = get_plan_settings().amount(billing_type=plan.billing_type, currency=currency)
        product_name = {
            "pt": "Plano Tarô Diário + Astrologia Semanal",
            "es": "Plan Tarot Diario + Astrología Semanal",
        }.get(language, "Daily Tarot + Weekly Astrology Plan")

        params = {
            "mode": "subscription" if plan.billing_type == "recurring" else "payment",
            "payment_method_types": ["card"],
            "line_items": [{
                "price_data": {
                    "currency": currency,
                    "unit_amount": amount,
                    "product_data": {"name": product_name},
                    **({"recurring": {"interval": "month"}} if plan.billing_type == "recurring" else {}),
                },
                "quantity": 1,
            }],
            "metadata": {
                "purpose": "daily_weekly_plan",
                "plan_id": str(plan.id),
                "user_id": str(plan.user_id),
                "billing_type": plan.billing_type,
                "currency": currency,
            },
            "success_url": f"{payment_settings.public_base_url}/api/plans/success",
            "cancel_url": f"{payment_settings.public_base_url}/api/plans/cancelled",
        }
        if plan.billing_type == "recurring":
            params["subscription_data"] = {
                "metadata": {
                    "purpose": "daily_weekly_plan",
                    "plan_id": str(plan.id),
                    "user_id": str(plan.user_id),
                }
            }

        try:
            session = stripe.checkout.Session.create(**params)
        except Exception as exc:
            raise PlanProviderError(f"Unable to create plan checkout: {exc}") from exc

        if not getattr(session, "url", None):
            raise PlanProviderError("Stripe did not return a checkout URL.")
        plan.currency = currency
        plan.amount_cents = amount
        plan.stripe_checkout_session_id = session.id
        db.commit()
        return str(session.url)

    def activate_from_checkout(self, *, db: Session, session: dict) -> DailyWeeklyPlanEntity | None:
        metadata = session.get("metadata") or {}
        if metadata.get("purpose") != "daily_weekly_plan":
            return None
        try:
            plan_id = int(metadata["plan_id"])
        except (KeyError, TypeError, ValueError):
            return None
        plan = db.get(DailyWeeklyPlanEntity, plan_id)
        if plan is None:
            return None

        now = datetime.now(timezone.utc)
        plan.status = "ACTIVE"
        plan.starts_at = plan.starts_at or now
        plan.stripe_checkout_session_id = str(session.get("id") or plan.stripe_checkout_session_id or "") or None
        plan.stripe_customer_id = str(session.get("customer") or "") or None
        subscription_id = str(session.get("subscription") or "") or None
        plan.stripe_subscription_id = subscription_id
        plan.cancel_at_period_end = False

        if plan.billing_type == "recurring" and subscription_id:
            plan.current_period_end = self._subscription_period_end(subscription_id) or (now + timedelta(days=31))
        else:
            plan.current_period_end = now + timedelta(days=30)

        location = self.profile_location(db, plan.user_id)
        if location:
            plan.schedule_timezone = str(location["current_timezone"])
        if plan.schedule_timezone:
            plan.next_daily_at = self.next_daily_occurrence(
                daily_time=plan.daily_time,
                timezone_name=plan.schedule_timezone,
                last_sent_at=plan.last_daily_sent_at,
                now=now,
            )
            plan.next_weekly_at = self.next_weekly_occurrence(
                weekday=plan.weekly_weekday,
                weekly_time=plan.weekly_time,
                timezone_name=plan.schedule_timezone,
                last_sent_at=plan.last_weekly_sent_at,
                now=now,
            )
        db.commit()
        db.refresh(plan)
        return plan

    def renew_subscription(self, *, db: Session, subscription_id: str, period_end: datetime | None = None) -> DailyWeeklyPlanEntity | None:
        plan = db.scalar(
            select(DailyWeeklyPlanEntity).where(DailyWeeklyPlanEntity.stripe_subscription_id == subscription_id)
        )
        if plan is None:
            return None
        plan.status = "CANCEL_AT_PERIOD_END" if plan.cancel_at_period_end else "ACTIVE"
        plan.current_period_end = period_end or self._subscription_period_end(subscription_id) or (datetime.now(timezone.utc) + timedelta(days=31))
        db.commit()
        return plan

    def mark_subscription_ended(self, *, db: Session, subscription_id: str) -> DailyWeeklyPlanEntity | None:
        plan = db.scalar(
            select(DailyWeeklyPlanEntity).where(DailyWeeklyPlanEntity.stripe_subscription_id == subscription_id)
        )
        if plan is None:
            return None
        plan.status = "EXPIRED"
        plan.next_daily_at = None
        plan.next_weekly_at = None
        db.commit()
        return plan

    def cancel_renewal(self, *, db: Session, plan: DailyWeeklyPlanEntity) -> None:
        if plan.billing_type == "one_time":
            plan.cancel_at_period_end = True
            plan.status = "CANCEL_AT_PERIOD_END"
            db.commit()
            return
        if not plan.stripe_subscription_id:
            raise ValueError("Subscription is not connected to Stripe.")
        payment_settings = get_payment_settings()
        if not payment_settings.stripe_secret_key:
            raise PlanConfigurationError("STRIPE_SECRET_KEY is not configured.")
        stripe.api_key = payment_settings.stripe_secret_key
        try:
            subscription = stripe.Subscription.modify(plan.stripe_subscription_id, cancel_at_period_end=True)
        except Exception as exc:
            raise PlanProviderError(f"Unable to cancel subscription renewal: {exc}") from exc
        plan.cancel_at_period_end = True
        plan.status = "CANCEL_AT_PERIOD_END"
        raw_end = getattr(subscription, "current_period_end", None)
        if raw_end:
            plan.current_period_end = datetime.fromtimestamp(int(raw_end), tz=timezone.utc)
        db.commit()

    @staticmethod
    def next_daily_occurrence(
        *,
        daily_time: time | None,
        timezone_name: str,
        last_sent_at: datetime | None,
        now: datetime | None = None,
    ) -> datetime | None:
        if daily_time is None:
            return None
        current = now or datetime.now(timezone.utc)
        tz = ZoneInfo(timezone_name)
        local_now = current.astimezone(tz)
        candidate_local = local_now.replace(
            hour=daily_time.hour, minute=daily_time.minute, second=0, microsecond=0
        )
        if candidate_local <= local_now:
            candidate_local += timedelta(days=1)
        candidate = candidate_local.astimezone(timezone.utc)
        if last_sent_at is not None:
            minimum = last_sent_at + timedelta(hours=24)
            if candidate < minimum:
                candidate = minimum
        return candidate

    @staticmethod
    def next_weekly_occurrence(
        *,
        weekday: int | None,
        weekly_time: time | None,
        timezone_name: str,
        last_sent_at: datetime | None,
        now: datetime | None = None,
    ) -> datetime | None:
        if weekday is None or weekly_time is None:
            return None
        current = now or datetime.now(timezone.utc)
        tz = ZoneInfo(timezone_name)
        local_now = current.astimezone(tz)
        days_ahead = (weekday - local_now.weekday()) % 7
        candidate_date = local_now.date() + timedelta(days=days_ahead)
        candidate_local = datetime.combine(candidate_date, weekly_time, tzinfo=tz)
        if candidate_local <= local_now:
            candidate_local += timedelta(days=7)
        candidate = candidate_local.astimezone(timezone.utc)
        if last_sent_at is not None:
            minimum = last_sent_at + timedelta(days=7)
            if candidate < minimum:
                candidate = minimum
        return candidate

    @staticmethod
    def _subscription_period_end(subscription_id: str) -> datetime | None:
        settings = get_payment_settings()
        if not settings.stripe_secret_key:
            return None
        stripe.api_key = settings.stripe_secret_key
        try:
            subscription = stripe.Subscription.retrieve(subscription_id)
            raw = getattr(subscription, "current_period_end", None)
            if raw:
                return datetime.fromtimestamp(int(raw), tz=timezone.utc)
        except Exception:
            return None
        return None


daily_weekly_plan_service = DailyWeeklyPlanService()
