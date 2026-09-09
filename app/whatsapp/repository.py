from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.persistence.models import (
    WhatsAppConversationEntity,
    WhatsAppMessageEventEntity,
    WhatsAppOutboundMessageEntity,
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

    def register_outbound_message(
        self,
        db: Session,
        *,
        whatsapp_message_id: str,
        to_number: str,
        text_body: str,
        provider_status: str | None = None,
    ) -> None:
        existing = db.scalar(
            select(WhatsAppOutboundMessageEntity.id)
            .where(
                WhatsAppOutboundMessageEntity.whatsapp_message_id
                == whatsapp_message_id
            )
        )
        if existing is not None:
            return

        db.add(
            WhatsAppOutboundMessageEntity(
                whatsapp_message_id=whatsapp_message_id,
                to_number=to_number,
                text_body=text_body,
                status="ACCEPTED",
                provider_status=provider_status,
            )
        )
        try:
            db.commit()
        except IntegrityError:
            db.rollback()

    def update_outbound_status(
        self,
        db: Session,
        *,
        whatsapp_message_id: str,
        status: str,
        recipient_id: str | None,
        error_code: int | None,
        error_title: str | None,
        error_message: str | None,
    ) -> None:
        outbound = db.scalar(
            select(WhatsAppOutboundMessageEntity)
            .where(
                WhatsAppOutboundMessageEntity.whatsapp_message_id
                == whatsapp_message_id
            )
        )

        if outbound is None:
            # Status webhooks can race the response persistence. Keep the event
            # observable even if we have no local message body yet.
            outbound = WhatsAppOutboundMessageEntity(
                whatsapp_message_id=whatsapp_message_id,
                to_number=recipient_id or "unknown",
                text_body="",
            )
            db.add(outbound)

        outbound.status = status.upper()
        outbound.provider_status = status
        outbound.error_code = error_code
        outbound.error_title = error_title
        outbound.error_message = error_message
        outbound.status_updated_at = datetime.now(timezone.utc)
        db.commit()

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
