from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.database.base import Base
from app.tarot.mystic_intuition import MysticIntuition


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
        payload = [intuition.to_dict() for intuition in intuitions]
        if row is None:
            row = MysticIntuitionEntity(reading_id=reading_id, payload=payload)
            db.add(row)
        else:
            row.payload = payload
        db.commit()

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
