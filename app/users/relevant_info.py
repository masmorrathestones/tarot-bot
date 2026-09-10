from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.database.base import Base
from app.persistence.models import UserEntity


class UserRelevantInformationEntity(Base):
    __tablename__ = "user_relevant_information"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    text: Mapped[str] = mapped_column(String(240), nullable=False)
    selected_for_next_reading: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class RelevantInformationService:
    def list_for_whatsapp(self, db: Session, whatsapp_number: str) -> tuple[int | None, list[UserRelevantInformationEntity]]:
        user = db.scalar(select(UserEntity).where(UserEntity.whatsapp_number == whatsapp_number))
        if user is None:
            return None, []
        rows = list(db.scalars(
            select(UserRelevantInformationEntity)
            .where(UserRelevantInformationEntity.user_id == user.id)
            .order_by(UserRelevantInformationEntity.id.asc())
        ))
        return user.id, rows

    def apply_selection(
        self,
        db: Session,
        *,
        user_id: int,
        selected_ids: list[int],
        new_information: str | None,
    ) -> None:
        rows = list(db.scalars(
            select(UserRelevantInformationEntity)
            .where(UserRelevantInformationEntity.user_id == user_id)
        ))
        allowed = {row.id for row in rows}
        selected = [value for value in selected_ids if value in allowed][:3]
        for row in rows:
            row.selected_for_next_reading = row.id in selected

        text_value = " ".join((new_information or "").split()).strip()[:240]
        if text_value:
            existing = next((r for r in rows if r.text.casefold() == text_value.casefold()), None)
            if existing is not None:
                existing.selected_for_next_reading = True
            else:
                db.add(UserRelevantInformationEntity(
                    user_id=user_id,
                    text=text_value,
                    selected_for_next_reading=True,
                ))
        db.commit()

    def consume_selected(self, db: Session, user_id: int) -> list[str]:
        rows = list(db.scalars(
            select(UserRelevantInformationEntity)
            .where(
                UserRelevantInformationEntity.user_id == user_id,
                UserRelevantInformationEntity.selected_for_next_reading.is_(True),
            )
            .order_by(UserRelevantInformationEntity.id.asc())
        ))
        result = [row.text for row in rows]
        for row in rows:
            row.selected_for_next_reading = False
        if rows:
            db.commit()
        return result


relevant_information_service = RelevantInformationService()
