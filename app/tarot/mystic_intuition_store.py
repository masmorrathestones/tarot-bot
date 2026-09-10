from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.database.base import Base
from app.persistence.models import ReadingEntity
from app.tarot.mystic_intuition import MysticIntuition, enforce_contextual_intuitions


class MysticIntuitionEntity(Base):
    __tablename__ = "reading_mystic_intuitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reading_id: Mapped[int] = mapped_column(
        ForeignKey("readings.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    payload: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )


class MysticIntuitionStore:
    def save(
        self,
        db: Session,
        reading_id: int,
        intuitions: list[MysticIntuition],
    ) -> None:
        row = db.scalar(
            select(MysticIntuitionEntity).where(
                MysticIntuitionEntity.reading_id == reading_id
            )
        )
        existing: list[MysticIntuition] = []
        if row is not None:
            for item in row.payload or []:
                if isinstance(item, dict):
                    try:
                        existing.append(MysticIntuition.from_dict(item))
                    except (TypeError, ValueError):
                        pass

        reading = db.get(ReadingEntity, reading_id)
        signals = []
        if reading is not None and isinstance(reading.profile_snapshot, dict):
            raw = reading.profile_snapshot.get("symbolic_signals") or []
            if isinstance(raw, list):
                signals = [item for item in raw if isinstance(item, dict)]

        combined = (existing + list(intuitions))[:2]
        combined = enforce_contextual_intuitions(combined, signals)
        payload = [intuition.to_dict() for intuition in combined]

        if row is None:
            row = MysticIntuitionEntity(reading_id=reading_id, payload=payload)
            db.add(row)
        else:
            row.payload = payload
        db.commit()

    def ensure_for_reading(self, db: Session, reading_id: int) -> None:
        """Persist forced contextual intuitions even when the normal random draw returned none."""
        reading = db.get(ReadingEntity, reading_id)
        if reading is None or not isinstance(reading.profile_snapshot, dict):
            return
        signals = reading.profile_snapshot.get("symbolic_signals") or []
        forced = enforce_contextual_intuitions([], signals if isinstance(signals, list) else [])
        if forced:
            self.save(db, reading_id, forced)

    def get(self, db: Session, reading_id: int) -> list[MysticIntuition]:
        row = db.scalar(
            select(MysticIntuitionEntity).where(
                MysticIntuitionEntity.reading_id == reading_id
            )
        )
        if row is None:
            return []

        result: list[MysticIntuition] = []
        for item in row.payload or []:
            if not isinstance(item, dict):
                continue
            try:
                result.append(MysticIntuition.from_dict(item))
            except (TypeError, ValueError):
                continue
        return result


mystic_intuition_store = MysticIntuitionStore()
