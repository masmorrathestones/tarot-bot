from __future__ import annotations

import os
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.provider import AIConfigurationError, AIProviderError
from app.past_life.ai import past_life_ai_service
from app.past_life.numerology import ARCANA, word_arcana_number
from app.payments.service import PaymentConfigurationError, PaymentProviderError, tarot_payment_service
from app.persistence.models import PastLifeReadingEntity, WhatsAppConversationEntity
from app.tarot.enums import Orientation
from app.tarot.models import DrawnCard, Spread, SpreadPosition
from app.tarot.service import tarot_draw_service
from app.users.service import UserNotFoundError, user_service
from app.whatsapp.i18n import normalize_language, t
from app.whatsapp.repository import whatsapp_repository
from app.whatsapp.ritual_state import whatsapp_tarot_flow_store


COMMANDS = {"vidas passadas", "vida passada", "past life", "past lives", "vidas pasadas", "/pastlife"}
CANCEL = {"cancel", "cancelar", "/cancel", "/cancelar"}
READY = {"pronto", "pronta", "ready", "listo", "lista"}
YES = {"sim", "s", "yes", "y", "sí", "si"}
NO = {"não", "nao", "n", "no"}
STATES = {
    "PAST_LIFE_AWAITING_PAYMENT", "PAST_LIFE_MEDITATING", "PAST_LIFE_AWAITING_WORD",
    "PAST_LIFE_AWAITING_THEME_CONFIRMATION", "PAST_LIFE_AWAITING_HELPFULNESS",
}
MIN_MEDITATION_SECONDS = 120


def _pick(language: str, en: str, pt: str, es: str) -> str:
    return {"en": en, "pt": pt, "es": es}[normalize_language(language)]


class PastLifeConversationService:
    def handles(self, *, state: str, text: str) -> bool:
        return state in STATES or text.strip().lower() in COMMANDS

    def handle_text(self, *, db: Session, from_number: str, display_name: str | None, text: str) -> list[str | dict]:
        clean = text.strip()
        command = clean.lower()
        try:
            user = user_service.get_by_whatsapp(db, from_number)
        except UserNotFoundError:
            return []
        conversation, _ = whatsapp_repository.get_or_create_conversation_by_number(
            db, whatsapp_number=from_number, user_id=user.id
        )
        language = normalize_language(conversation.language)

        if conversation.state in STATES and command in CANCEL:
            tarot_payment_service.cancel_pending_for_conversation(db=db, conversation_id=conversation.id)
            self._reset(db, conversation)
            return [_pick(language, "↩️ *Past Life Tarot canceled.*", "↩️ *Tarô de Vidas Passadas cancelado.*", "↩️ *Tarot de Vidas Pasadas cancelado.*"), t(language, "main_menu")]

        if command in COMMANDS:
            if conversation.state in STATES:
                tarot_payment_service.cancel_pending_for_conversation(db=db, conversation_id=conversation.id)
            whatsapp_tarot_flow_store.clear(db, conversation.id)
            try:
                payment = tarot_payment_service.create_checkout_session(
                    db=db, user_id=user.id, conversation_id=conversation.id,
                    language=language, purpose="past_life_reading",
                )
            except (PaymentConfigurationError, PaymentProviderError):
                self._reset(db, conversation)
                return [t(language, "payment_unavailable"), t(language, "main_menu")]
            conversation.state = "PAST_LIFE_AWAITING_PAYMENT"
            whatsapp_tarot_flow_store.save(db, conversation.id, {
                "past_life_payment_session_id": payment.provider_session_id,
                "payment_url": payment.checkout_url,
            })
            db.commit()
            intro = _pick(
                language,
                "🕯️ *PAST LIFE TAROT*\n\n🃏 Two spreads · *6 cards each*\n1️⃣ Past-life personality\n2️⃣ Past-life identity\n\n💰 Price: *US$2 / R$12*",
                "🕯️ *TARÔ DE VIDAS PASSADAS*\n\n🃏 Duas tiragens · *6 cartas cada*\n1️⃣ Personalidade da vida passada\n2️⃣ Identidade da vida passada\n\n💰 Valor: *US$ 2 / R$ 12*",
                "🕯️ *TAROT DE VIDAS PASADAS*\n\n🃏 Dos tiradas · *6 cartas cada una*\n1️⃣ Personalidad de la vida pasada\n2️⃣ Identidad de la vida pasada\n\n💰 Precio: *US$2 / R$12*",
            )
            payment_message = _pick(
                language,
                f"💳 *Continue to payment*\n\nChoose *US$2 or R$12*:\n{payment.checkout_url}\n\n🔒 _The meditation begins after confirmation._",
                f"💳 *Continue para o pagamento*\n\nEscolha *US$ 2 ou R$ 12*:\n{payment.checkout_url}\n\n🔒 _A meditação começa após a confirmação._",
                f"💳 *Continúa al pago*\n\nElige *US$2 o R$12*:\n{payment.checkout_url}\n\n🔒 _La meditación comienza tras la confirmación._",
            )
            return [intro, payment_message]

        if conversation.state == "PAST_LIFE_AWAITING_PAYMENT":
            url = str(whatsapp_tarot_flow_store.get(db, conversation.id).get("payment_url") or "")
            return [t(language, "payment_pending", url=url)]

        reading = self._latest(db, conversation.id)
        if reading is None:
            self._reset(db, conversation)
            return [t(language, "main_menu")]

        if conversation.state == "PAST_LIFE_MEDITATING":
            if command not in READY:
                return [self._meditation_prompt(language)]
            started = reading.meditation_started_at
            if started.tzinfo is None:
                started = started.replace(tzinfo=timezone.utc)
            elapsed = (datetime.now(timezone.utc) - started).total_seconds()
            if elapsed < MIN_MEDITATION_SECONDS:
                remaining = max(1, int((MIN_MEDITATION_SECONDS - elapsed + 59) // 60))
                return [_pick(language,
                    f"⏳ *Stay with the meditation a little longer*\n\nTake at least *{remaining} more minute(s)*. Let the question hold your attention and send *READY* again afterward.",
                    f"⏳ *Permaneça na meditação mais um pouco*\n\nDedique pelo menos mais *{remaining} minuto(s)*. Deixe a questão ocupar sua atenção e depois envie *PRONTO* novamente.",
                    f"⏳ *Permanece en la meditación un poco más*\n\nDedica al menos *{remaining} minuto(s) más*. Deja que la cuestión ocupe tu atención y luego envía *LISTO* nuevamente.")]
            reading.meditation_completed_at = datetime.now(timezone.utc)
            reading.status = "AWAITING_WORD"
            conversation.state = "PAST_LIFE_AWAITING_WORD"
            db.commit()
            return [_pick(language,
                "💭 *Your intuitive word*\n\nWithout overthinking, send the *first word* connected to your meditation that comes to mind.\n\n_Preferably a noun._",
                "💭 *Sua palavra intuitiva*\n\nSem pensar demais, envie a *primeira palavra* relacionada à meditação que vier à mente.\n\n_De preferência, um substantivo._",
                "💭 *Tu palabra intuitiva*\n\nSin pensarlo demasiado, envía la *primera palabra* relacionada con la meditación que te venga a la mente.\n\n_Preferiblemente un sustantivo._")]

        if conversation.state == "PAST_LIFE_AWAITING_WORD":
            try:
                arcana_number = word_arcana_number(clean)
            except ValueError:
                return [_pick(language, "Send one word containing letters.", "Envie uma palavra que contenha letras.", "Envía una palabra que contenga letras.")]
            reading.meditation_word = clean[:120]
            reading.word_arcana_number = arcana_number
            reading.word_arcana_name = ARCANA[arcana_number]
            cards = tarot_draw_service.draw(self._spread("PAST_LIFE_PERSONALITY"), allow_reversed=True)
            reading.personality_cards = serialize_cards(cards)
            try:
                analysis = past_life_ai_service.analyze_personality(
                    cards=cards, arcana_name=reading.word_arcana_name,
                    profile=reading.profile_snapshot, language=language,
                )
                theme = past_life_ai_service.infer_theme(
                    word=reading.meditation_word, arcana_name=reading.word_arcana_name,
                    profile=reading.profile_snapshot, language=language,
                )
            except (AIConfigurationError, AIProviderError, KeyError, ValueError):
                reading.status = "FAILED"
                db.commit()
                return [_pick(language, "I couldn't complete the analysis now. Your data was saved; please try again later.", "Não consegui concluir a análise agora. Seus dados foram salvos; tente novamente mais tarde.", "No pude completar el análisis ahora. Tus datos fueron guardados; inténtalo más tarde.")]
            reading.personality_analysis = analysis
            reading.theme_candidates = theme["candidates"]
            reading.selected_theme = str(theme["selected_theme"])
            reading.intuitive_question = str(theme["question"])
            reading.status = "AWAITING_THEME_CONFIRMATION"
            conversation.state = "PAST_LIFE_AWAITING_THEME_CONFIRMATION"
            db.commit()
            return [
                {"type": "image", "url": spread_url(reading.id, 1), "caption": _pick(language, "🃏 *FIRST SPREAD*\n_Past-life personality_", "🃏 *PRIMEIRA TIRAGEM*\n_Personalidade da vida passada_", "🃏 *PRIMERA TIRADA*\n_Personalidad de la vida pasada_")},
                analysis,
                f"🔮 *Intuitive question*\n\n{reading.intuitive_question}\n\n" + _pick(language, "💬 Reply *YES* or *NO*.", "💬 Responda *SIM* ou *NÃO*.", "💬 Responde *SÍ* o *NO*."),
            ]

        if conversation.state == "PAST_LIFE_AWAITING_THEME_CONFIRMATION":
            if command not in YES | NO:
                return [f"🔮 *Intuitive question*\n\n{reading.intuitive_question}\n\n" + _pick(language, "💬 Reply *YES* or *NO*.", "💬 Responda *SIM* ou *NÃO*.", "💬 Responde *SÍ* o *NO*.")]
            confirmed = command in YES
            reading.intuitive_answer = confirmed
            if not confirmed:
                try:
                    reading.selected_theme = past_life_ai_service.choose_alternate_theme(
                        candidates=reading.theme_candidates or [], rejected_theme=reading.selected_theme or "",
                        arcana_name=reading.word_arcana_name or "", profile=reading.profile_snapshot,
                        language=language,
                    )
                except (AIConfigurationError, AIProviderError, KeyError, ValueError):
                    pass
            cards = tarot_draw_service.draw(self._spread("PAST_LIFE_IDENTITY"), allow_reversed=True)
            reading.second_cards = serialize_cards(cards)
            try:
                final = past_life_ai_service.analyze_identity(
                    cards=cards, word=reading.meditation_word or "", arcana_name=reading.word_arcana_name or "",
                    theme=reading.selected_theme or "", profile=reading.profile_snapshot, language=language,
                )
            except (AIConfigurationError, AIProviderError):
                reading.status = "FAILED"
                db.commit()
                return [_pick(language, "The final analysis failed, but both spreads were saved.", "A análise final falhou, mas as duas tiragens foram salvas.", "El análisis final falló, pero ambas tiradas fueron guardadas.")]
            reading.final_analysis = final
            reading.status = "AWAITING_HELPFULNESS"
            conversation.state = "PAST_LIFE_AWAITING_HELPFULNESS"
            db.commit()
            return [
                {"type": "image", "url": spread_url(reading.id, 2), "caption": _pick(language, "🃏 *SECOND SPREAD*\n_Past-life identity_", "🃏 *SEGUNDA TIRAGEM*\n_Identidade da vida passada_", "🃏 *SEGUNDA TIRADA*\n_Identidad de la vida pasada_")},
                final,
                _pick(language, "✨ *Did this reading help?*\n\nDid it help you resolve or better understand your question?\n\n💬 Reply *YES* or *NO*.", "✨ *Esta tiragem ajudou?*\n\nEla ajudou você a sanar ou compreender melhor a sua questão?\n\n💬 Responda *SIM* ou *NÃO*.", "✨ *¿Esta tirada te ayudó?*\n\n¿Te ayudó a resolver o comprender mejor tu cuestión?\n\n💬 Responde *SÍ* o *NO*."),
            ]

        if conversation.state == "PAST_LIFE_AWAITING_HELPFULNESS":
            reading.helped_answer = True if command in YES else False if command in NO else None
            reading.helped_answer_text = clean[:1000]
            reading.status = "COMPLETED"
            reading.completed_at = datetime.now(timezone.utc)
            self._reset(db, conversation)
            return [_pick(language, "✨ *Thank you!* Your answer was saved.", "✨ *Obrigado!* Sua resposta foi salva.", "✨ *¡Gracias!* Tu respuesta fue guardada."), t(language, "main_menu")]

        return [t(language, "main_menu")]

    def resume_after_payment(self, *, db: Session, conversation_id: int, provider_session_id: str) -> tuple[str | None, list[str | dict]]:
        conversation = db.get(WhatsAppConversationEntity, conversation_id)
        if conversation is None or conversation.user_id is None or conversation.state != "PAST_LIFE_AWAITING_PAYMENT":
            return (conversation.whatsapp_number if conversation else None), []
        flow = whatsapp_tarot_flow_store.get(db, conversation.id)
        if str(flow.get("past_life_payment_session_id") or "") != provider_session_id:
            return conversation.whatsapp_number, []
        user = user_service.get(db, conversation.user_id)
        reading = PastLifeReadingEntity(
            user_id=user.id, conversation_id=conversation.id, status="AWAITING_MEDITATION",
            meditation_started_at=datetime.now(timezone.utc), profile_snapshot=self._profile(user),
        )
        db.add(reading)
        conversation.state = "PAST_LIFE_MEDITATING"
        whatsapp_tarot_flow_store.clear(db, conversation.id)
        db.commit()
        return conversation.whatsapp_number, [t(normalize_language(conversation.language), "payment_confirmed"), self._meditation_prompt(normalize_language(conversation.language))]

    def cancel_unpaid_payment(self, *, db: Session, conversation_id: int, provider_session_id: str) -> tuple[str | None, list[str | dict]]:
        conversation = db.get(WhatsAppConversationEntity, conversation_id)
        if conversation is None:
            return None, []
        flow = whatsapp_tarot_flow_store.get(db, conversation.id)
        if conversation.state != "PAST_LIFE_AWAITING_PAYMENT" or str(flow.get("past_life_payment_session_id") or "") != provider_session_id:
            return conversation.whatsapp_number, []
        language = normalize_language(conversation.language)
        self._reset(db, conversation)
        return conversation.whatsapp_number, [t(language, "payment_expired"), t(language, "main_menu")]

    @staticmethod
    def _latest(db: Session, conversation_id: int) -> PastLifeReadingEntity | None:
        return db.scalar(select(PastLifeReadingEntity).where(PastLifeReadingEntity.conversation_id == conversation_id).order_by(PastLifeReadingEntity.id.desc()).limit(1))

    @staticmethod
    def _profile(user) -> dict:
        p = user.profile
        return {"mbti": p.mbti if p else None, "natal_chart": p.natal_chart if p else None,
                "zodiac_sign": p.zodiac_sign if p else None, "personal_arcana": p.personal_arcana_name if p else None,
                "year_arcana": p.year_arcana_name if p else None}

    @staticmethod
    def _spread(code: str) -> Spread:
        return Spread(code=code, name=code, description="Six-card Past Life Tarot sequence", positions=tuple(
            SpreadPosition(index=i, code=f"CARD_{i}", name=f"Card {i}", description="Sequential symbolic position") for i in range(1, 7)
        ))

    @staticmethod
    def _meditation_prompt(language: str) -> str:
        return _pick(language,
            "🧘 *MEDITATION — AT LEAST 2 MINUTES*\n\n1️⃣ Decide what you want to know about a past life.\n2️⃣ Reflect on why this question matters to you.\n3️⃣ Set everything else aside and hold only that question in mind.\n\nYour focus may be an unresolved issue, a profession, a place or another specific concern.\n\n💬 Send *READY* only when your meditation feels complete.",
            "🧘 *MEDITAÇÃO — PELO MENOS 2 MINUTOS*\n\n1️⃣ Decida o que deseja saber sobre uma vida passada.\n2️⃣ Reflita por que essa questão é relevante para você.\n3️⃣ Deixe todo o resto de lado e mantenha apenas essa questão na mente.\n\nSeu foco pode ser uma questão mal resolvida, profissão, lugar ou outra inquietação específica.\n\n💬 Envie *PRONTO* somente quando sentir que concluiu a meditação.",
            "🧘 *MEDITACIÓN — AL MENOS 2 MINUTOS*\n\n1️⃣ Decide qué deseas saber sobre una vida pasada.\n2️⃣ Reflexiona por qué esa cuestión es relevante para ti.\n3️⃣ Deja todo lo demás a un lado y mantén solo esa cuestión en mente.\n\nTu enfoque puede ser una cuestión no resuelta, profesión, lugar u otra inquietud específica.\n\n💬 Envía *LISTO* solamente cuando termines la meditación.")

    @staticmethod
    def _reset(db: Session, conversation) -> None:
        whatsapp_tarot_flow_store.clear(db, conversation.id)
        conversation.state = "AWAITING_QUESTION"
        conversation.pending_question = None
        conversation.pending_context = None
        db.commit()


def serialize_cards(cards: list[DrawnCard]) -> list[dict]:
    return [{"index": c.position.index, "card_code": c.card.code, "orientation": c.orientation.value} for c in cards]


def reconstruct_cards(data: list[dict]) -> list[DrawnCard]:
    spread = PastLifeConversationService._spread("PAST_LIFE_MEDIA")
    deck = {card.code: card for card in tarot_draw_service.list_cards()}
    return [DrawnCard(position=spread.positions[int(item["index"]) - 1], card=deck[str(item["card_code"])], orientation=Orientation(str(item["orientation"]))) for item in data]


def spread_url(reading_id: int, draw_number: int) -> str:
    base = os.getenv("PUBLIC_BASE_URL", "https://tarot-bot-c1fv.onrender.com").rstrip("/")
    return f"{base}/api/assets/past-life/{reading_id}/{draw_number}.jpg"


past_life_conversation_service = PastLifeConversationService()
