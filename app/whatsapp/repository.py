from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.persistence.models import (
    WhatsAppConversationEntity,
    WhatsAppMessageEventEntity,
)


class WhatsAppRepository:
    def get_or_create_conversation(
        self,
        db: Session,
        *,
        user_id: int,
    ) -> WhatsAppConversationEntity:
        conversation = db.scalar(
            select(WhatsAppConversationEntity)
            .where(WhatsAppConversationEntity.user_id == user_id)
        )
        if conversation is not None:
            return conversation

        conversation = WhatsAppConversationEntity(
            user_id=user_id,
            state="AWAITING_QUESTION",
        )
        db.add(conversation)

        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            conversation = db.scalar(
                select(WhatsAppConversationEntity)
                .where(WhatsAppConversationEntity.user_id == user_id)
            )
            if conversation is None:
                raise

        return conversation

    def register_inbound_event(
        self,
        db: Session,
        *,
        whatsapp_message_id: str,
        from_number: str,
        display_name: str | None,
        message_type: str,
        text_body: str | None,
    ) -> bool:
        existing = db.scalar(
            select(WhatsAppMessageEventEntity.id)
            .where(
                WhatsAppMessageEventEntity.whatsapp_message_id
                == whatsapp_message_id
            )
        )
        if existing is not None:
            return False

        event = WhatsAppMessageEventEntity(
            whatsapp_message_id=whatsapp_message_id,
            from_number=from_number,
            display_name=display_name,
            message_type=message_type,
            text_body=text_body,
            status="RECEIVED",
        )
        db.add(event)

        try:
            db.commit()
            return True
        except IntegrityError:
            db.rollback()
            return False

    def mark_event_processed(
        self,
        db: Session,
        *,
        whatsapp_message_id: str,
    ) -> None:
        event = db.scalar(
            select(WhatsAppMessageEventEntity)
            .where(
                WhatsAppMessageEventEntity.whatsapp_message_id
                == whatsapp_message_id
            )
        )
        if event is None:
            return

        event.status = "PROCESSED"
        event.error_message = None
        event.processed_at = datetime.now(timezone.utc)
        db.commit()

    def mark_event_failed(
        self,
        db: Session,
        *,
        whatsapp_message_id: str,
        error_message: str,
    ) -> None:
        event = db.scalar(
            select(WhatsAppMessageEventEntity)
            .where(
                WhatsAppMessageEventEntity.whatsapp_message_id
                == whatsapp_message_id
            )
        )
        if event is None:
            return

        event.status = "FAILED"
        event.error_message = error_message[:5000]
        event.processed_at = datetime.now(timezone.utc)
        db.commit()


whatsapp_repository = WhatsAppRepository()
