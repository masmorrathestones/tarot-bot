from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import exists, or_, select

from app.database.session import SessionLocal
from app.social.x.campaign_loader import import_latest_campaign
from app.social.x.client import x_client
from app.social.x.config import get_x_settings
from app.social.x.models import ScheduledXPostEntity


async def x_scheduler_loop() -> None:
    settings = get_x_settings()
    if not settings.scheduler_enabled:
        return

    try:
        await asyncio.to_thread(import_latest_campaign)
    except Exception:
        pass

    while True:
        try:
            await asyncio.to_thread(process_due_x_posts)
        except Exception:
            pass
        await asyncio.sleep(settings.scheduler_interval_seconds)


def process_due_x_posts() -> int:
    db = SessionLocal()
    sent = 0
    try:
        now = datetime.now(timezone.utc)
        parent = ScheduledXPostEntity.__table__.alias("thread_parent")
        parent_is_sent = exists(
            select(parent.c.id).where(
                parent.c.source_key == ScheduledXPostEntity.parent_source_key,
                parent.c.status == "SENT",
                parent.c.x_post_id.is_not(None),
            )
        )
        due = list(
            db.scalars(
                select(ScheduledXPostEntity)
                .where(
                    ScheduledXPostEntity.status == "PENDING",
                    ScheduledXPostEntity.scheduled_at <= now,
                    or_(
                        ScheduledXPostEntity.parent_source_key.is_(None),
                        parent_is_sent,
                    ),
                )
                .order_by(ScheduledXPostEntity.scheduled_at, ScheduledXPostEntity.id)
                .limit(10)
                .with_for_update(skip_locked=True)
            ).all()
        )

        for row in due:
            row.status = "PROCESSING"
            row.last_attempt_at = now
        if due:
            db.commit()

        for claimed in due:
            row = db.get(ScheduledXPostEntity, claimed.id)
            if row is None or row.status != "PROCESSING":
                continue
            try:
                reply_to_post_id = None
                if row.parent_source_key:
                    parent_row = db.scalar(
                        select(ScheduledXPostEntity).where(
                            ScheduledXPostEntity.source_key == row.parent_source_key
                        )
                    )
                    if parent_row is None or parent_row.status != "SENT" or not parent_row.x_post_id:
                        raise RuntimeError(
                            f"Thread parent is not ready: {row.parent_source_key}"
                        )
                    reply_to_post_id = parent_row.x_post_id

                x_post_id = x_client.create_post(
                    row.text,
                    media_path=row.media_path,
                    reply_to_post_id=reply_to_post_id,
                )
                finished_at = datetime.now(timezone.utc)
                row.status = "SENT"
                row.x_post_id = x_post_id
                row.sent_at = finished_at
                row.error_message = None
                db.commit()
                sent += 1
            except Exception as exc:
                row.status = "FAILED"
                row.error_message = str(exc)[:2000]
                db.commit()
        return sent
    finally:
        db.close()
