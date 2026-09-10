from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from sqlalchemy import select

from app.database.session import SessionLocal
from app.social.x.client import x_client
from app.social.x.config import get_x_settings
from app.social.x.models import ScheduledXPostEntity


async def x_scheduler_loop() -> None:
    settings = get_x_settings()
    if not settings.scheduler_enabled:
        return
    while True:
        try:
            await asyncio.to_thread(process_due_x_posts)
        except Exception:
            # Never let one scheduler iteration bring down the web process.
            pass
        await asyncio.sleep(settings.scheduler_interval_seconds)


def process_due_x_posts() -> int:
    db = SessionLocal()
    sent = 0
    try:
        now = datetime.now(timezone.utc)
        due = list(
            db.scalars(
                select(ScheduledXPostEntity)
                .where(
                    ScheduledXPostEntity.status == "PENDING",
                    ScheduledXPostEntity.scheduled_at <= now,
                )
                .order_by(ScheduledXPostEntity.scheduled_at, ScheduledXPostEntity.id)
                .limit(10)
                .with_for_update(skip_locked=True)
            ).all()
        )

        # Claim rows before making external requests so concurrent workers do not
        # publish the same post twice.
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
                x_post_id = x_client.create_post(row.text)
                finished_at = datetime.now(timezone.utc)
                row.status = "SENT"
                row.x_post_id = x_post_id
                row.sent_at = finished_at
                row.error_message = None
                db.commit()
                sent += 1
            except Exception as exc:
                # Do not auto-retry: if X accepted the post but the response was
                # lost, an automatic retry could create a duplicate. Failed jobs
                # can be retried explicitly through the management endpoint.
                row.status = "FAILED"
                row.error_message = str(exc)[:2000]
                db.commit()
        return sent
    finally:
        db.close()
