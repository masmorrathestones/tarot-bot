from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.provider import AIConfigurationError, AIProviderError
from app.dreams.ai import dream_ai_service
from app.dreams.matcher import match_dream_symbols
from app.dreams.models import DreamInterpretationEntity
from app.payments.service import PaymentConfigurationError, PaymentProviderError, tarot_payment_service
from app.persistence.models import WhatsAppConversationEntity
from app.users.relevant_info import relevant_information_service
from app.users.service import UserNotFoundError, user_service
from app.whatsapp.i18n import normalize_language, t
from app.whatsapp.repository import whatsapp_repository
from app.whatsapp.ritual_state import whatsapp_tarot_flow_store

COMMANDS = {"sonho", "sonhos", "interpretar sonho", "dream", "dreams", "sueño", "sueños", "/dream"}
CANCEL = {"cancel", "cancelar", "/cancel", "/cancelar"}
STATES = {"DREAM_AWAITING_TEXT", "DREAM_AWAITING_PAYMENT", "DREAM_ASKING_CONTEXT"}


def _pick(language: str, en: str, pt: str, es: str) -> str:
    return {"en": en, "pt": pt, "es": es}[normalize_language(language)]


class DreamConversationService:
    def handles(self, *, state: str, text: str) -> bool:
        return state in STATES or text.strip().casefold() in COMMANDS

    def handle_text(self, *, db: Session, from_number: str, display_name: str | None, text: str) -> list[str | dict]:
        clean = text.strip()
        command = clean.casefold()
        try:
            user = user_service.get_by_whatsapp(db, from_number)
        except UserNotFoundError:
            return []
        conversation, _ = whatsapp_repository.get_or_create_conversation_by_number(db, whatsapp_number=from_number, user_id=user.id)
        language = normalize_language(conversation.language)

        if conversation.state in STATES and command in CANCEL:
            tarot_payment_service.cancel_pending_for_conversation(db=db, conversation_id=conversation.id)
            self._reset(db, conversation)
            return [_pick(language, "↩️ *Dream interpretation canceled.*", "↩️ *Interpretação de sonhos cancelada.*", "↩️ *Interpretación de sueños cancelada.*"), t(language, "main_menu")]

        if command in COMMANDS:
            if conversation.state in STATES:
                tarot_payment_service.cancel_pending_for_conversation(db=db, conversation_id=conversation.id)
            whatsapp_tarot_flow_store.clear(db, conversation.id)
            conversation.state = "DREAM_AWAITING_TEXT"
            db.commit()
            return [_pick(language,
                "🌙 *DREAM INTERPRETATION*\n\nA layered reading of your dream's symbols, language and personal context.\n\n💰 *US$3 / R$18*\n\n✍️ Send your complete dream in one message, with as much detail as possible: people, places, colors, objects, actions, feelings and exact phrases.",
                "🌙 *INTERPRETAÇÃO DE SONHOS*\n\nUma leitura em camadas dos símbolos, da linguagem e do contexto pessoal do seu sonho.\n\n💰 *US$ 3 / R$ 18*\n\n✍️ Envie o sonho completo em uma única mensagem, com o máximo de detalhes possível: pessoas, lugares, cores, objetos, ações, sensações e frases exatas.",
                "🌙 *INTERPRETACIÓN DE SUEÑOS*\n\nUna lectura en capas de los símbolos, el lenguaje y el contexto personal de tu sueño.\n\n💰 *US$3 / R$18*\n\n✍️ Envía el sueño completo en un solo mensaje, con todos los detalles posibles: personas, lugares, colores, objetos, acciones, sensaciones y frases exactas.")]

        if conversation.state == "DREAM_AWAITING_TEXT":
            if len(clean) < 40:
                return [_pick(language, "Please describe the dream in at least a few complete sentences.", "Descreva o sonho com pelo menos algumas frases completas.", "Describe el sueño con al menos algunas frases completas.")]
            reading = DreamInterpretationEntity(user_id=user.id, conversation_id=conversation.id, language=language, status="AWAITING_PAYMENT", dream_text=clean, answers=[], current_question_index=0)
            db.add(reading)
            db.flush()
            try:
                payment = tarot_payment_service.create_checkout_session(db=db, user_id=user.id, conversation_id=conversation.id, language=language, purpose="dream_interpretation")
            except (PaymentConfigurationError, PaymentProviderError):
                db.rollback()
                self._reset(db, conversation)
                return [t(language, "payment_unavailable"), t(language, "main_menu")]
            reading.payment_id = payment.id
            conversation.state = "DREAM_AWAITING_PAYMENT"
            whatsapp_tarot_flow_store.save(db, conversation.id, {"dream_payment_session_id": payment.provider_session_id, "payment_url": payment.checkout_url, "dream_reading_id": reading.id})
            db.commit()
            return [_pick(language,
                f"💳 *Dream received*\n\nContinue to payment — *US$3 or R$18*:\n{payment.checkout_url}\n\n🔒 _Your analysis starts after confirmation._",
                f"💳 *Sonho recebido*\n\nContinue para o pagamento — *US$ 3 ou R$ 18*:\n{payment.checkout_url}\n\n🔒 _Sua análise começa após a confirmação._",
                f"💳 *Sueño recibido*\n\nContinúa al pago — *US$3 o R$18*:\n{payment.checkout_url}\n\n🔒 _Tu análisis comienza tras la confirmación._")]

        if conversation.state == "DREAM_AWAITING_PAYMENT":
            url = str(whatsapp_tarot_flow_store.get(db, conversation.id).get("payment_url") or "")
            return [t(language, "payment_pending", url=url)]

        reading = self._latest(db, conversation.id)
        if reading is None:
            self._reset(db, conversation)
            return [t(language, "main_menu")]

        if conversation.state == "DREAM_ASKING_CONTEXT":
            questions = reading.contextual_questions or []
            index = reading.current_question_index
            if index >= len(questions):
                return self._complete(db, conversation, reading)
            answers = list(reading.answers or [])
            answers.append({"question": questions[index], "answer": clean})
            reading.answers = answers
            reading.current_question_index = index + 1
            db.commit()
            if reading.current_question_index < len(questions):
                return [self._question(language, questions[reading.current_question_index], reading.current_question_index, len(questions))]
            return self._complete(db, conversation, reading)

        return [t(language, "main_menu")]

    def resume_after_payment(self, *, db: Session, conversation_id: int, provider_session_id: str) -> tuple[str | None, list[str | dict]]:
        conversation = db.get(WhatsAppConversationEntity, conversation_id)
        if conversation is None or conversation.state != "DREAM_AWAITING_PAYMENT":
            return (conversation.whatsapp_number if conversation else None), []
        flow = whatsapp_tarot_flow_store.get(db, conversation.id)
        if str(flow.get("dream_payment_session_id") or "") != provider_session_id:
            return conversation.whatsapp_number, []
        reading = db.get(DreamInterpretationEntity, int(flow["dream_reading_id"]))
        if reading is None:
            return conversation.whatsapp_number, []
        language = normalize_language(conversation.language)
        try:
            initial = dream_ai_service.prepare_questions(dream=reading.dream_text, language=language)
        except (AIConfigurationError, AIProviderError, ValueError, KeyError):
            reading.status = "FAILED_INITIAL_ANALYSIS"
            db.commit()
            return conversation.whatsapp_number, [_pick(language, "Your dream was saved, but I couldn't prepare the analysis now. Please try again later.", "Seu sonho foi salvo, mas não consegui preparar a análise agora. Tente novamente mais tarde.", "Tu sueño fue guardado, pero no pude preparar el análisis ahora. Inténtalo más tarde.")]
        reading.linguistic_analogies = initial["linguistic_analogies"]
        reading.contextual_questions = initial["questions"]
        reading.status = "ASKING_CONTEXT"
        reading.current_question_index = 0
        whatsapp_tarot_flow_store.clear(db, conversation.id)
        if not reading.contextual_questions:
            conversation.state = "DREAM_ASKING_CONTEXT"
            db.commit()
            return conversation.whatsapp_number, [t(language, "payment_confirmed"), *self._complete(db, conversation, reading)]
        conversation.state = "DREAM_ASKING_CONTEXT"
        db.commit()
        messages = [t(language, "payment_confirmed"), self._analogy_message(language, reading.linguistic_analogies or []), _pick(language, "🧭 *A few questions will help me distinguish the strongest meanings.*", "🧭 *Algumas perguntas vão me ajudar a distinguir os sentidos mais fortes.*", "🧭 *Algunas preguntas me ayudarán a distinguir los sentidos más fuertes.*"), self._question(language, reading.contextual_questions[0], 0, len(reading.contextual_questions))]
        return conversation.whatsapp_number, messages

    def cancel_unpaid_payment(self, *, db: Session, conversation_id: int, provider_session_id: str) -> tuple[str | None, list[str | dict]]:
        conversation = db.get(WhatsAppConversationEntity, conversation_id)
        if conversation is None:
            return None, []
        flow = whatsapp_tarot_flow_store.get(db, conversation.id)
        if conversation.state != "DREAM_AWAITING_PAYMENT" or str(flow.get("dream_payment_session_id") or "") != provider_session_id:
            return conversation.whatsapp_number, []
        language = normalize_language(conversation.language)
        self._reset(db, conversation)
        return conversation.whatsapp_number, [t(language, "payment_expired"), t(language, "main_menu")]

    def _complete(self, db: Session, conversation, reading: DreamInterpretationEntity) -> list[str | dict]:
        language = normalize_language(conversation.language)
        reading.status = "ANALYZING"
        db.commit()
        try:
            facts = dream_ai_service.extract_facts(dream=reading.dream_text, questions_and_answers=reading.answers or [], language=language)
            relevant_information_service.add_many(db, user_id=reading.user_id, texts=facts)
            symbols = match_dream_symbols(db, reading.dream_text, language=language)
            analysis = dream_ai_service.final_analysis(dream=reading.dream_text, analogies=reading.linguistic_analogies or [], questions_and_answers=reading.answers or [], symbols=symbols, language=language)
        except (AIConfigurationError, AIProviderError, ValueError, KeyError):
            reading.status = "FAILED_FINAL_ANALYSIS"
            db.commit()
            return [_pick(language, "Your answers were saved, but the final analysis failed. It can be retried without asking again.", "Suas respostas foram salvas, mas a análise final falhou. Ela pode ser refeita sem perguntar tudo novamente.", "Tus respuestas fueron guardadas, pero falló el análisis final. Puede reintentarse sin volver a preguntar.")]
        reading.relevant_facts = facts
        reading.matched_symbols = symbols
        reading.final_analysis = analysis
        reading.status = "COMPLETED"
        reading.completed_at = datetime.now(timezone.utc)
        self._reset(db, conversation)
        return [_pick(language, "🌙 *YOUR DREAM INTERPRETATION*", "🌙 *SUA INTERPRETAÇÃO DO SONHO*", "🌙 *TU INTERPRETACIÓN DEL SUEÑO*"), analysis, t(language, "main_menu")]

    @staticmethod
    def _latest(db: Session, conversation_id: int) -> DreamInterpretationEntity | None:
        return db.scalar(select(DreamInterpretationEntity).where(DreamInterpretationEntity.conversation_id == conversation_id).order_by(DreamInterpretationEntity.id.desc()).limit(1))

    @staticmethod
    def _question(language: str, question: str, index: int, total: int) -> str:
        return _pick(language, f"❓ *Question {index + 1} of {total}*\n\n{question}", f"❓ *Pergunta {index + 1} de {total}*\n\n{question}", f"❓ *Pregunta {index + 1} de {total}*\n\n{question}")

    @staticmethod
    def _analogy_message(language: str, analogies: list[dict]) -> str:
        if not analogies:
            return _pick(language, "🔤 No strong sound association was forced.", "🔤 Nenhuma associação sonora forte foi forçada.", "🔤 No se forzó ninguna asociación sonora débil.")
        title = _pick(language, "🔤 *Possible language echoes*", "🔤 *Possíveis ecos de linguagem*", "🔤 *Posibles ecos del lenguaje*")
        return title + "\n\n" + "\n".join(f"• *{a.get('text', '')}* — {a.get('evidence', '')}" for a in analogies)

    @staticmethod
    def _reset(db: Session, conversation) -> None:
        whatsapp_tarot_flow_store.clear(db, conversation.id)
        conversation.state = "AWAITING_QUESTION"
        conversation.pending_question = None
        conversation.pending_context = None
        db.commit()


dream_conversation_service = DreamConversationService()
