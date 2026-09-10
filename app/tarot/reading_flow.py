from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.ai.provider import AIConfigurationError, AIProviderError
from app.ai.service import UserSymbolicProfile, tarot_interpretation_service
from app.persistence.models import ReadingEntity
from app.tarot.mystic_intuition_store import mystic_intuition_store
from app.tarot.persistence_service import reading_persistence_service
from app.tarot.service import tarot_draw_service
from app.users.service import user_service


class InvalidSpreadError(ValueError):
    pass


@dataclass(frozen=True)
class CreatedReading:
    reading: ReadingEntity


class TarotReadingFlow:
    def create(
        self,
        *,
        db: Session,
        user_id: int,
        spread_code: str,
        question: str,
        context: str | None,
        allow_reversed: bool = True,
    ) -> ReadingEntity:
        spread = tarot_draw_service.get_spread(spread_code)
        if spread is None:
            raise InvalidSpreadError(f"Unknown spread: {spread_code}")

        user = user_service.get(db, user_id)
        drawn = tarot_draw_service.draw(
            spread=spread,
            allow_reversed=allow_reversed,
        )

        persisted = reading_persistence_service.create_pending(
            db=db,
            user_id=user.id,
            spread=spread,
            question=question,
            context=context,
            allow_reversed=allow_reversed,
            drawn_cards=drawn,
        )

        profile = UserSymbolicProfile.from_snapshot(persisted.profile_snapshot)
        intuitions = mystic_intuition_store.get(db, persisted.id)

        try:
            interpretation = tarot_interpretation_service.interpret(
                question=question,
                context=context,
                spread=spread,
                drawn_cards=drawn,
                profile=profile,
                mystic_intuitions=intuitions,
            )
        except (AIConfigurationError, AIProviderError) as exc:
            reading_persistence_service.mark_failed(
                db=db,
                reading_id=persisted.id,
                error_message=str(exc),
            )
            raise

        return reading_persistence_service.mark_completed(
            db=db,
            reading_id=persisted.id,
            narrative=interpretation.narrative,
            card_analysis=interpretation.card_analysis,
            synthesis=interpretation.synthesis,
        )


tarot_reading_flow = TarotReadingFlow()
