from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.ai.provider import AIConfigurationError, AIProviderError
from app.ai.service import UserSymbolicProfile, tarot_interpretation_service
from app.ai.spread_selector import SpreadSelectionError, spread_selection_service
from app.tarot.enums import Orientation
from app.tarot.models import DrawnCard
from app.tarot.mystic_intuition import MysticIntuition, draw_mystic_intuitions
from app.tarot.mystic_intuition_store import mystic_intuition_store
from app.tarot.persistence_service import reading_persistence_service
from app.tarot.ritual import FallenCandidate, ritual_draw_engine
from app.tarot.service import tarot_draw_service
from app.users.service import UserNotFoundError, user_service
from app.whatsapp.conversation import whatsapp_conversation_service as legacy_conversation_service
from app.whatsapp.i18n import normalize_language, output_language_instruction, t
from app.whatsapp.repository import whatsapp_repository
from app.whatsapp.ritual_state import whatsapp_tarot_flow_store
from app.whatsapp.tarot_media import (
    card_back_image_url,
    card_caption,
    card_image_url,
    spread_image_url,
)


TAROT_COMMANDS = {"tarot", "/tarot", "reading", "/reading", "leitura", "lectura", "new", "/new"}
CANCEL_COMMANDS = {"cancel", "/cancel", "cancelar", "/cancelar"}
SKIP_ANSWERS = {"skip", "pular", "omitir"}
RITUAL_STATES = {
    "RITUAL_AWAITING_QUESTION",
    "RITUAL_AWAITING_CONTEXT",
    "RITUAL_DRAWING",
    "RITUAL_AWAITING_FALLEN_CHOICE",
    "RITUAL_ANALYZING",
}


def _pick(language: str, en: str, pt: str, es: str) -> str:
    return {"en": en, "pt": pt, "es": es}.get(normalize_language(language), en)


class RitualWhatsAppConversationService:
    def handle_text(
        self,
        *,
        db: Session,
        from_number: str,
        display_name: str | None,
        text: str,
    ) -> list[str | dict]:
        clean = text.strip()
        command = clean.lower()

        try:
            user = user_service.get_by_whatsapp(db, from_number)
        except UserNotFoundError:
            user = None

        if user is None:
            return legacy_conversation_service.handle_text(
                db=db,
                from_number=from_number,
                display_name=display_name,
                text=text,
            )

        conversation, _ = whatsapp_repository.get_or_create_conversation_by_number(
            db,
            whatsapp_number=from_number,
            user_id=user.id,
        )
        language = normalize_language(conversation.language)

        if conversation.state in RITUAL_STATES and command in CANCEL_COMMANDS:
            self._cancel(db, conversation)
            return [t(language, "tarot_cancelled"), self._main_menu_text(language)]

        if command in TAROT_COMMANDS:
            whatsapp_tarot_flow_store.clear(db, conversation.id)
            conversation.state = "RITUAL_AWAITING_QUESTION"
            conversation.pending_question = None
            conversation.pending_context = None
            db.commit()
            return [self._with_cancel(t(language, "reading_started"), language)]

        state = conversation.state
        if state not in RITUAL_STATES:
            return legacy_conversation_service.handle_text(
                db=db,
                from_number=from_number,
                display_name=display_name,
                text=text,
            )

        if state == "RITUAL_AWAITING_QUESTION":
            if not clean:
                return [self._with_cancel(t(language, "send_question"), language)]

            payload = {
                "question": clean[:500],
                "context": None,
                "spread_code": None,
                "drawn": [],
                "has_fallen": False,
                "fallen_candidates": [],
                "mystic_intuitions": [],
                "language": language,
            }
            whatsapp_tarot_flow_store.save(db, conversation.id, payload)
            conversation.state = "RITUAL_AWAITING_CONTEXT"
            db.commit()
            return [self._with_cancel(t(language, "context_prompt"), language)]

        if state == "RITUAL_AWAITING_CONTEXT":
            payload = whatsapp_tarot_flow_store.get(db, conversation.id)
            question = str(payload.get("question") or "").strip()
            if not question:
                conversation.state = "RITUAL_AWAITING_QUESTION"
                db.commit()
                return [self._with_cancel(_pick(
                    language,
                    "I lost the pending question. Please send it again.",
                    "Perdi a pergunta pendente. Envie-a novamente.",
                    "Perdí la pregunta pendiente. Envíala de nuevo.",
                ), language)]

            context = None if command in SKIP_ANSWERS else clean[:1000]
            payload["context"] = context
            payload["language"] = language

            try:
                spread_code = spread_selection_service.choose_spread(
                    question=question,
                    context=context,
                    profile_snapshot={**self._profile_snapshot(user), "language": language},
                )
            except (AIConfigurationError, AIProviderError, SpreadSelectionError):
                self._cancel(db, conversation)
                return [t(language, "select_spread_failed"), self._main_menu_text(language)]

            payload["spread_code"] = spread_code
            payload["drawn"] = []
            payload["has_fallen"] = False
            payload["fallen_candidates"] = []
            payload["mystic_intuitions"] = [
                intuition.to_dict() for intuition in draw_mystic_intuitions()
            ]
            conversation.state = "RITUAL_DRAWING"
            whatsapp_tarot_flow_store.save(db, conversation.id, payload)
            db.commit()

            return [t(language, "shuffling"), *self._continue_draw(db, user, conversation, payload)]

        if state == "RITUAL_AWAITING_FALLEN_CHOICE":
            payload = whatsapp_tarot_flow_store.get(db, conversation.id)
            candidates_data = payload.get("fallen_candidates") or []
            candidates = [
                FallenCandidate.from_dict(item)
                for item in candidates_data
                if isinstance(item, dict)
            ]

            try:
                choice = int(clean)
            except ValueError:
                choice = 0

            if choice < 1 or choice > len(candidates):
                return [self._fallen_choice_prompt(len(candidates), language)]

            spread = tarot_draw_service.get_spread(str(payload.get("spread_code") or ""))
            if spread is None:
                self._cancel(db, conversation)
                return [t(language, "spread_unavailable"), self._main_menu_text(language)]

            drawn_data = payload.get("drawn") or []
            position_index = len(drawn_data)
            if position_index >= len(spread.positions):
                return self._finish_draw(db, user, conversation, payload)

            drawn = ritual_draw_engine.materialize_candidate(
                candidate=candidates[choice - 1],
                position=spread.positions[position_index],
            )
            drawn_data.append(self._serialize_drawn(drawn))
            payload["drawn"] = drawn_data
            payload["has_fallen"] = True
            payload["fallen_candidates"] = []
            conversation.state = "RITUAL_DRAWING"
            whatsapp_tarot_flow_store.save(db, conversation.id, payload)
            db.commit()

            return [self._card_message(drawn, language), *self._continue_draw(db, user, conversation, payload)]

        if state == "RITUAL_DRAWING":
            payload = whatsapp_tarot_flow_store.get(db, conversation.id)
            return self._continue_draw(db, user, conversation, payload)

        if state == "RITUAL_ANALYZING":
            return [self._with_cancel(t(language, "already_analyzing"), language)]

        return [self._main_menu_text(language)]

    def _continue_draw(self, db: Session, user, conversation, payload: dict) -> list[str | dict]:
        language = normalize_language(conversation.language)
        spread = tarot_draw_service.get_spread(str(payload.get("spread_code") or ""))
        if spread is None:
            self._cancel(db, conversation)
            return [t(language, "spread_unavailable"), self._main_menu_text(language)]

        messages: list[str | dict] = []
        drawn_data = list(payload.get("drawn") or [])

        while len(drawn_data) < len(spread.positions):
            draw_index = len(drawn_data)
            excluded_codes = {
                str(item.get("card_code"))
                for item in drawn_data
                if isinstance(item, dict) and item.get("card_code")
            }

            if ritual_draw_engine.should_cards_fall(
                draw_index=draw_index,
                has_fallen_before=bool(payload.get("has_fallen")),
            ):
                candidates = ritual_draw_engine.fallen_candidates(
                    excluded_codes=excluded_codes,
                    allow_reversed=True,
                )
                payload["fallen_candidates"] = [item.to_dict() for item in candidates]
                payload["has_fallen"] = True
                conversation.state = "RITUAL_AWAITING_FALLEN_CHOICE"
                whatsapp_tarot_flow_store.save(db, conversation.id, payload)
                db.commit()

                count = len(candidates)
                messages.extend([
                    t(language, "fallen_intro"),
                    {
                        "type": "image",
                        "url": card_back_image_url(count),
                        "caption": self._fallen_choice_prompt(count, language),
                    },
                ])
                return messages

            drawn = ritual_draw_engine.draw_one(
                position=spread.positions[draw_index],
                excluded_codes=excluded_codes,
                allow_reversed=True,
            )
            drawn_data.append(self._serialize_drawn(drawn))
            payload["drawn"] = drawn_data
            whatsapp_tarot_flow_store.save(db, conversation.id, payload)
            messages.append(self._card_message(drawn, language))

        messages.extend(self._finish_draw(db, user, conversation, payload))
        return messages

    def _finish_draw(self, db: Session, user, conversation, payload: dict) -> list[str | dict]:
        language = normalize_language(conversation.language)
        spread = tarot_draw_service.get_spread(str(payload.get("spread_code") or ""))
        if spread is None:
            self._cancel(db, conversation)
            return [t(language, "spread_unavailable"), self._main_menu_text(language)]

        drawn_cards = self._deserialize_drawn(spread, payload.get("drawn") or [])
        if len(drawn_cards) != len(spread.positions):
            raise ValueError("The ritual draw ended with an incomplete spread.")

        reading = reading_persistence_service.create_pending(
            db=db,
            user_id=user.id,
            spread=spread,
            question=str(payload.get("question") or ""),
            context=payload.get("context"),
            allow_reversed=True,
            drawn_cards=drawn_cards,
            language=language,
        )

        intuitions = self._deserialize_intuitions(payload.get("mystic_intuitions") or [])
        if intuitions:
            mystic_intuition_store.save(db, reading.id, intuitions)

        conversation.state = "RITUAL_ANALYZING"
        whatsapp_tarot_flow_store.save(
            db,
            conversation.id,
            {"analysis_reading_id": reading.id, "language": language},
        )
        db.commit()

        return [
            {
                "type": "image",
                "url": spread_image_url(reading.id),
                "caption": t(language, "reading_caption", id=reading.id),
            },
            {"type": "analysis_wait", "language": language},
            {"type": "deferred_tarot_analysis", "reading_id": reading.id},
        ]

    def complete_analysis(
        self,
        *,
        db: Session,
        from_number: str,
        reading_id: int,
    ) -> list[str | dict]:
        reading = reading_persistence_service.get(db, reading_id)
        spread = tarot_draw_service.get_spread(reading.spread_code)
        if spread is None:
            reading_persistence_service.mark_failed(
                db=db,
                reading_id=reading.id,
                error_message="Persisted spread definition is unavailable.",
            )
            return []

        language = normalize_language((reading.profile_snapshot or {}).get("language"))
        language_instruction = output_language_instruction(language)
        localized_context = (
            f"{reading.context}\n\n{language_instruction}"
            if reading.context
            else language_instruction
        )

        drawn_cards = reading_persistence_service.reconstruct_drawn_cards(reading)
        profile = UserSymbolicProfile.from_snapshot(reading.profile_snapshot)
        mystic_intuitions = mystic_intuition_store.get(db, reading.id)

        try:
            interpretation = tarot_interpretation_service.interpret(
                question=reading.question,
                context=localized_context,
                spread=spread,
                drawn_cards=drawn_cards,
                profile=profile,
                mystic_intuitions=mystic_intuitions,
            )
            completed = reading_persistence_service.mark_completed(
                db=db,
                reading_id=reading.id,
                narrative=interpretation.narrative,
                card_analysis=interpretation.card_analysis,
                synthesis=interpretation.synthesis,
            )
        except (AIConfigurationError, AIProviderError) as exc:
            reading_persistence_service.mark_failed(
                db=db,
                reading_id=reading.id,
                error_message=str(exc),
            )
            completed = None

        try:
            user = user_service.get_by_whatsapp(db, from_number)
        except UserNotFoundError:
            return []

        conversation, _ = whatsapp_repository.get_or_create_conversation_by_number(
            db,
            whatsapp_number=from_number,
            user_id=user.id,
        )
        language = normalize_language(conversation.language)
        flow = whatsapp_tarot_flow_store.get(db, conversation.id)

        if (
            conversation.state != "RITUAL_ANALYZING"
            or int(flow.get("analysis_reading_id") or 0) != reading_id
        ):
            return []

        whatsapp_tarot_flow_store.clear(db, conversation.id)
        conversation.state = "AWAITING_QUESTION"
        conversation.pending_question = None
        conversation.pending_context = None
        db.commit()

        if completed is None:
            failure = _pick(
                language,
                f"Your cards were drawn and saved, but the AI interpretation failed. Reading ID: {reading_id}.",
                f"Suas cartas foram tiradas e salvas, mas a interpretação da IA falhou. ID da leitura: {reading_id}.",
                f"Tus cartas fueron sacadas y guardadas, pero falló la interpretación de la IA. ID de lectura: {reading_id}.",
            )
            return [failure, self._main_menu_text(language)]

        return [
            f"*{t(language, 'overall_label')}*\n\n{completed.narrative or ''}",
            f"*{t(language, 'cards_label')}*\n\n{completed.card_analysis or ''}",
            f"*{t(language, 'synthesis_label')}*\n\n{completed.synthesis or ''}",
            self._main_menu_text(language),
        ]

    def _cancel(self, db: Session, conversation) -> None:
        whatsapp_tarot_flow_store.clear(db, conversation.id)
        conversation.state = "AWAITING_QUESTION"
        conversation.pending_question = None
        conversation.pending_context = None
        db.commit()

    @staticmethod
    def _profile_snapshot(user) -> dict[str, Any]:
        p = user.profile
        return {
            "name": user.name,
            "whatsapp_number": user.whatsapp_number,
            "sun_sign": p.sun_sign if p else None,
            "moon_sign": p.moon_sign if p else None,
            "rising_sign": p.rising_sign if p else None,
            "mbti": p.mbti if p else None,
            "birth_date": p.birth_date.isoformat() if p and p.birth_date else None,
            "birth_time": p.birth_time.isoformat() if p and p.birth_time else None,
            "birth_place": p.birth_place if p else None,
            "birth_latitude": p.birth_latitude if p else None,
            "birth_longitude": p.birth_longitude if p else None,
            "birth_timezone": p.birth_timezone if p else None,
            "zodiac_sign": p.zodiac_sign if p else None,
            "personal_number": p.personal_number if p else None,
            "personal_arcana_number": p.personal_arcana_number if p else None,
            "personal_arcana_name": p.personal_arcana_name if p else None,
            "year_arcana_number": p.year_arcana_number if p else None,
            "year_arcana_name": p.year_arcana_name if p else None,
            "year_arcana_reference_year": p.year_arcana_reference_year if p else None,
            "natal_chart": p.natal_chart if p else None,
        }

    @staticmethod
    def _serialize_drawn(drawn: DrawnCard) -> dict:
        return {"card_code": drawn.card.code, "orientation": drawn.orientation.value}

    @staticmethod
    def _deserialize_drawn(spread, data: list[dict]) -> list[DrawnCard]:
        result: list[DrawnCard] = []
        cards = {card.code: card for card in tarot_draw_service.list_cards()}
        for index, stored in enumerate(data):
            if index >= len(spread.positions):
                break
            card = cards.get(str(stored.get("card_code") or ""))
            if card is None:
                raise ValueError("Stored ritual card no longer exists in the deck.")
            result.append(
                DrawnCard(
                    position=spread.positions[index],
                    card=card,
                    orientation=Orientation(str(stored.get("orientation") or "upright")),
                )
            )
        return result

    @staticmethod
    def _deserialize_intuitions(data: list[dict]) -> list[MysticIntuition]:
        result: list[MysticIntuition] = []
        for item in data:
            if not isinstance(item, dict):
                continue
            try:
                result.append(MysticIntuition.from_dict(item))
            except (TypeError, ValueError):
                continue
        return result

    @staticmethod
    def _card_message(drawn: DrawnCard, language: str) -> dict:
        return {
            "type": "image",
            "url": card_image_url(drawn.card.code, drawn.orientation),
            "caption": card_caption(
                card=drawn.card,
                orientation=drawn.orientation,
                card_number=drawn.position.index,
                language=language,
            ),
        }

    @classmethod
    def _fallen_choice_prompt(cls, count: int, language: str) -> str:
        options = ", ".join(str(index) for index in range(1, count + 1))
        return cls._with_cancel(t(language, "fallen_choice", options=options), language)

    @staticmethod
    def _with_cancel(text: str, language: str) -> str:
        return t(language, "with_cancel", text=text)

    @staticmethod
    def _main_menu_text(language: str = "en") -> str:
        return t(language, "main_menu")


ritual_whatsapp_conversation_service = RitualWhatsAppConversationService()
