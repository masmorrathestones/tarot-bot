from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, func, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.database.base import Base


class WhatsAppTarotFlowEntity(Base):
    __tablename__ = "whatsapp_tarot_flows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("whatsapp_conversations.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class WhatsAppTarotFlowStore:
    def get(self, db: Session, conversation_id: int) -> dict:
        row = db.scalar(
            select(WhatsAppTarotFlowEntity).where(
                WhatsAppTarotFlowEntity.conversation_id == conversation_id
            )
        )
        return dict(row.payload or {}) if row else {}

    def save(self, db: Session, conversation_id: int, payload: dict) -> None:
        row = db.scalar(
            select(WhatsAppTarotFlowEntity).where(
                WhatsAppTarotFlowEntity.conversation_id == conversation_id
            )
        )
        if row is None:
            row = WhatsAppTarotFlowEntity(
                conversation_id=conversation_id,
                payload=dict(payload),
            )
            db.add(row)
        else:
            row.payload = dict(payload)
        db.commit()

    def clear(self, db: Session, conversation_id: int) -> None:
        row = db.scalar(
            select(WhatsAppTarotFlowEntity).where(
                WhatsAppTarotFlowEntity.conversation_id == conversation_id
            )
        )
        if row is not None:
            db.delete(row)
            db.commit()


whatsapp_tarot_flow_store = WhatsAppTarotFlowStore()
