from __future__ import annotations

import asyncio
import secrets
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.session import SessionLocal
from app.plans.ai import plan_analysis_service
from app.plans.astrology import calculate_weekly_transits
from app.plans.config import get_plan_settings
from app.plans.models import DailyWeeklyPlanEntity, PlanDeliveryEntity
from app.plans.service import daily_weekly_plan_service
from app.tarot.enums import Orientation
from app.tarot.mystic_intuition import MYSTIC_INTUITION_TYPES
from app.tarot.service import tarot_draw_service
from app.users.service import user_service
from app.whatsapp.i18n import normalize_language
from app.whatsapp.repository import whatsapp_repository
from app.whatsapp.tarot_media import card_image_url
from app.whatsapp.webhook import _send_outgoing


async def plan_scheduler_loop() -> None:
    settings = get_plan_settings()
    if not settings.scheduler_enabled:
        return
    while True:
        try:
            await asyncio.to_thread(process_due_plan_deliveries)
        except Exception:
            # A scheduler iteration must never bring down the web process.
            pass
        await asyncio.sleep(settings.scheduler_interval_seconds)


def process_due_plan_deliveries() -> int:
    processed = 0
    db = SessionLocal()
    try:
        now = datetime.now(timezone.utc)
        due = db.scalars(
            select(DailyWeeklyPlanEntity)
            .where(
                DailyWeeklyPlanEntity.status.in_(["ACTIVE", "CANCEL_AT_PERIOD_END"]),
                or_(DailyWeeklyPlanEntity.current_period_end.is_(None), DailyWeeklyPlanEntity.current_period_end > now),
                or_(
                    DailyWeeklyPlanEntity.next_daily_at <= now,
                    DailyWeeklyPlanEntity.next_weekly_at <= now,
                ),
            )
            .order_by(DailyWeeklyPlanEntity.id)
            .limit(25)
        ).all()

        for plan in due:
            if plan.current_period_end is not None and plan.current_period_end <= now:
                plan.status = "EXPIRED"
                plan.next_daily_at = None
                plan.next_weekly_at = None
                db.commit()
                continue
            if plan.next_daily_at is not None and plan.next_daily_at <= now:
                if _process_daily(db, plan, plan.next_daily_at):
                    processed += 1
            now = datetime.now(timezone.utc)
            if plan.next_weekly_at is not None and plan.next_weekly_at <= now:
                if _process_weekly(db, plan, plan.next_weekly_at):
                    processed += 1
        return processed
    finally:
        db.close()


def _claim_delivery(db: Session, plan: DailyWeeklyPlanEntity, delivery_type: str, scheduled_for: datetime) -> PlanDeliveryEntity | None:
    delivery = PlanDeliveryEntity(
        plan_id=plan.id,
        user_id=plan.user_id,
        delivery_type=delivery_type,
        scheduled_for=scheduled_for,
        status="PROCESSING",
    )
    db.add(delivery)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return None
    db.refresh(delivery)
    return delivery


def _process_daily(db: Session, plan: DailyWeeklyPlanEntity, scheduled_for: datetime) -> bool:
    delivery = _claim_delivery(db, plan, "DAILY_TAROT", scheduled_for)
    if delivery is None:
        plan.next_daily_at = daily_weekly_plan_service.next_daily_occurrence(
            daily_time=plan.daily_time,
            timezone_name=plan.schedule_timezone or "UTC",
            last_sent_at=plan.last_daily_sent_at or scheduled_for,
        )
        db.commit()
        return False

    try:
        user = user_service.get(db, plan.user_id)
        conversation, _ = whatsapp_repository.get_or_create_conversation_by_number(
            db,
            whatsapp_number=user.whatsapp_number,
            user_id=user.id,
        )
        language = normalize_language(conversation.language)
        cards = tarot_draw_service.list_cards()
        card = cards[secrets.randbelow(len(cards))]
        orientation = Orientation.REVERSED if secrets.randbelow(2) else Orientation.UPRIGHT
        alignment = MYSTIC_INTUITION_TYPES[secrets.randbelow(len(MYSTIC_INTUITION_TYPES))]
        weight = secrets.randbelow(11)  # Required daily range: 0..10 inclusive.
        p = user.profile
        analysis = plan_analysis_service.daily_card_analysis(
            card=card,
            orientation=orientation,
            language=language,
            personal_arcana=p.personal_arcana_name if p else None,
            year_arcana=p.year_arcana_name if p else None,
            mbti=p.mbti if p else None,
            intuition_alignment=alignment,
            intuition_weight=weight,
        )
        message = {
            "type": "image",
            "url": card_image_url(card.code, orientation),
            "caption": analysis,
        }
        _send_and_record(db, user.whatsapp_number, message)

        now = datetime.now(timezone.utc)
        delivery.status = "SENT"
        delivery.card_code = card.code
        delivery.orientation = orientation.value
        delivery.content = analysis
        delivery.sent_at = now
        plan.last_daily_sent_at = now
        plan.next_daily_at = daily_weekly_plan_service.next_daily_occurrence(
            daily_time=plan.daily_time,
            timezone_name=plan.schedule_timezone or "UTC",
            last_sent_at=now,
            now=now,
        )
        db.commit()
        return True
    except Exception as exc:
        delivery.status = "FAILED"
        delivery.error_message = str(exc)[:2000]
        # Retry this delivery later without allowing rapid duplicate attempts.
        plan.next_daily_at = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        plan.next_daily_at = plan.next_daily_at + __import__("datetime").timedelta(minutes=15)
        db.commit()
        return False


def _process_weekly(db: Session, plan: DailyWeeklyPlanEntity, scheduled_for: datetime) -> bool:
    delivery = _claim_delivery(db, plan, "WEEKLY_ASTROLOGY", scheduled_for)
    if delivery is None:
        plan.next_weekly_at = daily_weekly_plan_service.next_weekly_occurrence(
            weekday=plan.weekly_weekday,
            weekly_time=plan.weekly_time,
            timezone_name=plan.schedule_timezone or "UTC",
            last_sent_at=plan.last_weekly_sent_at or scheduled_for,
        )
        db.commit()
        return False

    try:
        user = user_service.get(db, plan.user_id)
        p = user.profile
        location = daily_weekly_plan_service.profile_location(db, user.id)
        if not p or not p.natal_chart or not location:
            raise ValueError("Weekly astrology requires a complete natal chart and current location.")
        conversation, _ = whatsapp_repository.get_or_create_conversation_by_number(
            db,
            whatsapp_number=user.whatsapp_number,
            user_id=user.id,
        )
        language = normalize_language(conversation.language)
        tz_name = str(location["current_timezone"])
        local_now = datetime.now(timezone.utc).astimezone(ZoneInfo(tz_name))
        transits = calculate_weekly_transits(start_local=local_now, natal_chart=p.natal_chart)
        analysis = plan_analysis_service.weekly_astrology_analysis(
            natal_chart=p.natal_chart,
            current_place=str(location["current_place"]),
            current_timezone=tz_name,
            weekly_transits=transits,
            language=language,
            generated_at=datetime.now(timezone.utc),
        )
        heading = {
            "pt": "🌌 *Sua análise astrológica da semana*\n\n",
            "es": "🌌 *Tu análisis astrológico de la semana*\n\n",
        }.get(language, "🌌 *Your weekly astrology analysis*\n\n")
        content = heading + analysis
        _send_and_record(db, user.whatsapp_number, content)

        now = datetime.now(timezone.utc)
        delivery.status = "SENT"
        delivery.content = analysis
        delivery.sent_at = now
        plan.last_weekly_sent_at = now
        plan.next_weekly_at = daily_weekly_plan_service.next_weekly_occurrence(
            weekday=plan.weekly_weekday,
            weekly_time=plan.weekly_time,
            timezone_name=plan.schedule_timezone or tz_name,
            last_sent_at=now,
            now=now,
        )
        db.commit()
        return True
    except Exception as exc:
        delivery.status = "FAILED"
        delivery.error_message = str(exc)[:2000]
        plan.next_weekly_at = datetime.now(timezone.utc).replace(second=0, microsecond=0)
        plan.next_weekly_at = plan.next_weekly_at + __import__("datetime").timedelta(minutes=30)
        db.commit()
        return False


def _send_and_record(db: Session, to: str, message: str | dict) -> None:
    sent_messages = _send_outgoing(to=to, message=message)
    for sent in sent_messages:
        whatsapp_repository.register_outbound_message(
            db,
            whatsapp_message_id=sent["id"],
            to_number=to,
            text_body=sent["body"],
            provider_status=sent.get("status"),
        )
