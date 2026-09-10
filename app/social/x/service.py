from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.social.x.models import ScheduledXPostEntity


class XScheduledPostNotFoundError(ValueError):
    pass


class XScheduledPostStateError(ValueError):
    pass


class XScheduleService:
    def schedule(
        self,
        *,
        db: Session,
        text: str,
        scheduled_at: datetime,
        language: str | None = None,
    ) -> ScheduledXPostEntity:
        if scheduled_at.utcoffset() is None:
            raise ValueError("scheduled_at must include a timezone offset.")
        normalized_text = text.strip()
        if not normalized_text:
            raise ValueError("Post text cannot be empty.")

        row = ScheduledXPostEntity(
            text=normalized_text,
            language=(language.strip().lower() if language else None),
            scheduled_at=scheduled_at.astimezone(timezone.utc),
            status="PENDING",
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row

    def list(
        self,
        *,
        db: Session,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ScheduledXPostEntity]:
        stmt = select(ScheduledXPostEntity).order_by(
            ScheduledXPostEntity.scheduled_at.desc(),
            ScheduledXPostEntity.id.desc(),
        )
        if status:
            stmt = stmt.where(ScheduledXPostEntity.status == status.strip().upper())
        return list(db.scalars(stmt.limit(max(1, min(limit, 100)))).all())

    def get(self, *, db: Session, post_id: int) -> ScheduledXPostEntity:
        row = db.get(ScheduledXPostEntity, post_id)
        if row is None:
            raise XScheduledPostNotFoundError("Scheduled X post not found.")
        return row

    def cancel(self, *, db: Session, post_id: int) -> ScheduledXPostEntity:
        row = self.get(db=db, post_id=post_id)
        if row.status != "PENDING":
            raise XScheduledPostStateError(
                f"Only PENDING posts can be cancelled. Current status: {row.status}."
            )
        row.status = "CANCELLED"
        db.commit()
        db.refresh(row)
        return row

    def retry(self, *, db: Session, post_id: int) -> ScheduledXPostEntity:
        row = self.get(db=db, post_id=post_id)
        if row.status != "FAILED":
            raise XScheduledPostStateError(
                f"Only FAILED posts can be retried. Current status: {row.status}."
            )
        row.status = "PENDING"
        row.error_message = None
        row.scheduled_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(row)
        return row


x_schedule_service = XScheduleService()
