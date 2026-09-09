from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.ai.config import get_ai_settings
from app.persistence.models import DrawnCardEntity, ReadingEntity
from app.tarot.enums import Orientation
from app.tarot.models import DrawnCard, Spread, SpreadPosition
from app.tarot.service import tarot_draw_service
from app.users.service import user_service


class ReadingNotFoundError(ValueError):
    pass


class ReadingRetryNotAllowedError(ValueError):
    pass


class ReadingPersistenceService:
    def create_pending(
        self,
        *,
        db: Session,
        user_id: int,
        spread: Spread,
        question: str,
        context: str | None,
        allow_reversed: bool,
        drawn_cards: list[DrawnCard],
    ) -> ReadingEntity:
        user = user_service.get(db, user_id)
        p = user.profile

        snapshot = {
            "name": user.name,
            "whatsapp_number": user.whatsapp_number,
            "sun_sign": p.sun_sign if p else None,
            "moon_sign": p.moon_sign if p else None,
            "rising_sign": p.rising_sign if p else None,
            "mbti": p.mbti if p else None,
        }

        reading = ReadingEntity(
            user_id=user.id,
            deck_code="Rider-Waite-Smith",
            spread_code=spread.code,
            question=question,
            context=context,
            allow_reversed=allow_reversed,
            profile_snapshot=snapshot,
            status="PENDING",
            retry_count=0,
            last_attempt_at=datetime.now(timezone.utc),
            ai_model=get_ai_settings().model,
            prompt_version="v1",
            knowledge_version="banzhaf-v1",
        )

        reading.drawn_cards = [
            DrawnCardEntity(
                card_code=item.card.code,
                card_name=item.card.name,
                position_index=item.position.index,
                position_code=item.position.code,
                position_name=item.position.name,
                position_description=item.position.description,
                orientation=item.orientation.value,
            )
            for item in drawn_cards
        ]

        db.add(reading)

        # Commit the cards BEFORE the AI call. A failed AI request therefore
        # cannot cause a redraw on the historical reading.
        db.commit()
        db.refresh(reading)
        return self.get(db, reading.id)

    def begin_retry(
        self,
        *,
        db: Session,
        reading_id: int,
    ) -> ReadingEntity:
        # Lock the row so two requests cannot start the same retry at once.
        reading = db.scalar(
            select(ReadingEntity)
            .options(selectinload(ReadingEntity.drawn_cards))
            .where(ReadingEntity.id == reading_id)
            .with_for_update()
        )

        if reading is None:
            db.rollback()
            raise ReadingNotFoundError("Reading not found.")

        if reading.status != "FAILED":
            db.rollback()
            raise ReadingRetryNotAllowedError(
                "Only FAILED readings can be retried. "
                f"Current status is {reading.status}."
            )

        reading.status = "RETRYING"
        reading.retry_count += 1
        reading.last_attempt_at = datetime.now(timezone.utc)
        reading.error_message = None
        db.commit()
        return self.get(db, reading_id)

    def mark_completed(
        self,
        *,
        db: Session,
        reading_id: int,
        narrative: str,
        card_analysis: str,
        synthesis: str,
    ) -> ReadingEntity:
        reading = self.get(db, reading_id)
        reading.status = "COMPLETED"
        reading.narrative = narrative
        reading.card_analysis = card_analysis
        reading.synthesis = synthesis
        reading.error_message = None
        reading.completed_at = datetime.now(timezone.utc)
        db.commit()
        return self.get(db, reading_id)

    def mark_failed(
        self, *, db: Session, reading_id: int, error_message: str
    ) -> ReadingEntity:
        reading = self.get(db, reading_id)
        reading.status = "FAILED"
        reading.error_message = error_message
        db.commit()
        return self.get(db, reading_id)

    def get(self, db: Session, reading_id: int) -> ReadingEntity:
        reading = db.scalar(
            select(ReadingEntity)
            .options(selectinload(ReadingEntity.drawn_cards))
            .where(ReadingEntity.id == reading_id)
        )
        if reading is None:
            raise ReadingNotFoundError("Reading not found.")
        return reading

    def reconstruct_drawn_cards(
        self, reading: ReadingEntity
    ) -> list[DrawnCard]:
        result = []

        for stored in reading.drawn_cards:
            card = next(
                (
                    card for card in tarot_draw_service.list_cards()
                    if card.code == stored.card_code
                ),
                None,
            )
            if card is None:
                raise RuntimeError(
                    f"Unknown persisted card code: {stored.card_code}"
                )

            result.append(
                DrawnCard(
                    position=SpreadPosition(
                        index=stored.position_index,
                        code=stored.position_code,
                        name=stored.position_name,
                        description=stored.position_description,
                    ),
                    card=card,
                    orientation=Orientation(stored.orientation),
                )
            )

        return result


reading_persistence_service = ReadingPersistenceService()
