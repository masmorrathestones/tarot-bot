from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.models import ReadingEntity, ReadingRatingEntity
from app.users.service import UserNotFoundError, user_service
from app.whatsapp.i18n import normalize_language, t
from app.whatsapp.repository import whatsapp_repository


RATING_COMMANDS = {
    "rate", "/rate", "rate reading", "rate reading", "rating",
    "avaliar", "/avaliar", "avaliar tiragem", "avaliar leitura",
    "calificar", "/calificar", "calificar tirada", "calificar lectura",
}
CANCEL_COMMANDS = {"cancel", "/cancel", "cancelar", "/cancelar"}
SKIP_COMMANDS = {"skip", "pular", "omitir", "sem observação", "sem observacao", "sin observación", "sin observacion"}


def _pick(language: str, en: str, pt: str, es: str) -> str:
    return {"en": en, "pt": pt, "es": es}.get(normalize_language(language), en)


class ReadingRatingWhatsAppService:
    def handles(self, *, state: str, text: str) -> bool:
        command = text.strip().lower()
        if state.startswith("RATING_"):
            return True
        if state.startswith(("RITUAL_", "PLAN_")):
            return False
        return command in RATING_COMMANDS

    def handle_text(
        self,
        *,
        db: Session,
        from_number: str,
        text: str,
    ) -> list[str] | None:
        clean = text.strip()
        command = clean.lower()

        try:
            user = user_service.get_by_whatsapp(db, from_number)
        except UserNotFoundError:
            return None

        conversation, _ = whatsapp_repository.get_or_create_conversation_by_number(
            db,
            whatsapp_number=from_number,
            user_id=user.id,
        )
        language = normalize_language(conversation.language)

        if conversation.state.startswith("RATING_") and command in CANCEL_COMMANDS:
            conversation.state = "AWAITING_QUESTION"
            db.commit()
            return [
                _pick(language, "Rating canceled.", "Avaliação cancelada.", "Calificación cancelada."),
                t(language, "main_menu"),
            ]

        if command in RATING_COMMANDS and not conversation.state.startswith("RATING_"):
            readings = self._recent_readings(db, user.id)
            if not readings:
                return [
                    _pick(
                        language,
                        "You do not have a completed Tarot reading to rate yet.",
                        "Você ainda não tem uma tiragem concluída para avaliar.",
                        "Todavía no tienes una tirada completada para calificar.",
                    ),
                    t(language, "main_menu"),
                ]

            conversation.state = "RATING_PICK"
            db.commit()
            lines = [
                _pick(
                    language,
                    "⭐ Which reading would you like to rate? Reply with the number:",
                    "⭐ Qual tiragem você quer avaliar? Responda com o número:",
                    "⭐ ¿Qué tirada quieres calificar? Responde con el número:",
                )
            ]
            for index, reading in enumerate(readings, start=1):
                question = " ".join((reading.question or "").split())
                if len(question) > 110:
                    question = question[:107].rstrip() + "..."
                lines.append(f"{index} — {question}")
            lines.append(
                _pick(language, "Send CANCEL to go back.", "Envie CANCELAR para voltar.", "Envía CANCELAR para volver.")
            )
            return ["\n".join(lines)]

        if conversation.state == "RATING_PICK":
            readings = self._recent_readings(db, user.id)
            try:
                choice = int(clean)
            except ValueError:
                choice = 0
            if choice < 1 or choice > len(readings):
                return [_pick(language, "Choose one of the listed numbers.", "Escolha um dos números listados.", "Elige uno de los números de la lista.")]

            reading = readings[choice - 1]
            conversation.state = f"RATING_STARS_{reading.id}"
            db.commit()
            return [
                _pick(
                    language,
                    "How many stars do you give this reading? Reply with a number from 1 to 5. ⭐",
                    "Quantas estrelas você dá para essa tiragem? Responda com um número de 1 a 5. ⭐",
                    "¿Cuántas estrellas le das a esta tirada? Responde con un número del 1 al 5. ⭐",
                )
            ]

        if conversation.state.startswith("RATING_STARS_"):
            reading_id = self._state_reading_id(conversation.state, "RATING_STARS_")
            reading = self._owned_reading(db, reading_id, user.id)
            if reading is None:
                conversation.state = "AWAITING_QUESTION"
                db.commit()
                return [t(language, "main_menu")]

            try:
                stars = int(clean)
            except ValueError:
                stars = 0
            if stars < 1 or stars > 5:
                return [_pick(language, "Send a number from 1 to 5.", "Envie um número de 1 a 5.", "Envía un número del 1 al 5.")]

            conversation.state = f"RATING_NOTE_{reading.id}_{stars}"
            db.commit()
            return [
                _pick(
                    language,
                    "Would you like to leave an observation about the reading? Send it now, or reply SKIP.",
                    "Quer deixar uma observação sobre a tiragem? Envie agora, ou responda PULAR.",
                    "¿Quieres dejar una observación sobre la tirada? Envíala ahora, o responde OMITIR.",
                )
            ]

        if conversation.state.startswith("RATING_NOTE_"):
            parsed = self._parse_note_state(conversation.state)
            if parsed is None:
                conversation.state = "AWAITING_QUESTION"
                db.commit()
                return [t(language, "main_menu")]
            reading_id, stars = parsed
            reading = self._owned_reading(db, reading_id, user.id)
            if reading is None:
                conversation.state = "AWAITING_QUESTION"
                db.commit()
                return [t(language, "main_menu")]

            note = None if command in SKIP_COMMANDS else clean[:2000]
            rating = db.scalar(
                select(ReadingRatingEntity).where(ReadingRatingEntity.reading_id == reading.id)
            )
            if rating is None:
                rating = ReadingRatingEntity(
                    reading_id=reading.id,
                    user_id=user.id,
                    stars=stars,
                    note=note,
                )
                db.add(rating)
            else:
                rating.stars = stars
                rating.note = note
                rating.user_id = user.id

            conversation.state = "AWAITING_QUESTION"
            db.commit()
            return [
                _pick(
                    language,
                    f"Obrigado pela avaliação de {stars} estrela(s)! ✨" if language == "pt" else f"Thanks for your {stars}-star rating! ✨",
                    f"Obrigado pela avaliação de {stars} estrela(s)! ✨",
                    f"¡Gracias por tu calificación de {stars} estrella(s)! ✨",
                ),
                t(language, "main_menu"),
            ]

        return None

    @staticmethod
    def _recent_readings(db: Session, user_id: int) -> list[ReadingEntity]:
        statement = (
            select(ReadingEntity)
            .where(ReadingEntity.user_id == user_id, ReadingEntity.status == "COMPLETED")
            .order_by(ReadingEntity.completed_at.desc(), ReadingEntity.id.desc())
            .limit(5)
        )
        return list(db.scalars(statement).all())

    @staticmethod
    def _owned_reading(db: Session, reading_id: int, user_id: int) -> ReadingEntity | None:
        if reading_id <= 0:
            return None
        return db.scalar(
            select(ReadingEntity).where(
                ReadingEntity.id == reading_id,
                ReadingEntity.user_id == user_id,
                ReadingEntity.status == "COMPLETED",
            )
        )

    @staticmethod
    def _state_reading_id(state: str, prefix: str) -> int:
        try:
            return int(state[len(prefix):])
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _parse_note_state(state: str) -> tuple[int, int] | None:
        raw = state[len("RATING_NOTE_"):]
        parts = raw.rsplit("_", 1)
        if len(parts) != 2:
            return None
        try:
            return int(parts[0]), int(parts[1])
        except ValueError:
            return None


reading_rating_whatsapp_service = ReadingRatingWhatsAppService()
