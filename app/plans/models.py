from datetime import datetime, time
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, Time, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DailyWeeklyPlanEntity(Base):
    __tablename__ = "daily_weekly_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    status: Mapped[str] = mapped_column(String(24), nullable=False, default="DRAFT", index=True)
    billing_type: Mapped[Optional[str]] = mapped_column(String(20))
    currency: Mapped[Optional[str]] = mapped_column(String(3))
    amount_cents: Mapped[Optional[int]] = mapped_column(Integer)

    daily_time: Mapped[Optional[time]] = mapped_column(Time())
    weekly_weekday: Mapped[Optional[int]] = mapped_column(Integer)
    weekly_time: Mapped[Optional[time]] = mapped_column(Time())
    schedule_timezone: Mapped[Optional[str]] = mapped_column(String(80))

    checkout_token: Mapped[Optional[str]] = mapped_column(String(80), unique=True, index=True)
    stripe_checkout_session_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(255), index=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)

    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    current_period_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cancel_at_period_end: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    next_daily_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    next_weekly_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)
    last_daily_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_weekly_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class PlanDeliveryEntity(Base):
    __tablename__ = "plan_deliveries"
    __table_args__ = (
        UniqueConstraint("plan_id", "delivery_type", "scheduled_for", name="uq_plan_delivery_slot"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("daily_weekly_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    delivery_type: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PROCESSING", index=True)
    card_code: Mapped[Optional[str]] = mapped_column(String(80))
    orientation: Mapped[Optional[str]] = mapped_column(String(20))
    content: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
