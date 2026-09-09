import json
from datetime import date, datetime

import httpx
from sqlalchemy.orm import Session

from app.ai.provider import AIConfigurationError, AIProviderError
from app.tarot.persistence_service import reading_persistence_service
from app.tarot.reading_flow import InvalidSpreadError, tarot_reading_flow
from app.users.service import UserNotFoundError, user_service
from app.whatsapp.arcana_media import arcana_image_url
from app.whatsapp.astrology import (
    BirthPlaceNotFoundError,
    BirthTimezoneNotFoundError,
    calculate_natal_chart,
    format_natal_chart,
    geocode_birth_place,
)
from app.whatsapp.i18n import (
    language_selection_prompt,
    normalize_language,
    parse_language_choice,
    t,
)
from app.whatsapp.personality import (
    MBTI_QUESTIONS,
    calculate_mbti,
    format_question,
    initial_scores,
    mbti_description,
    score_answer,
)
from app.whatsapp.profile_calculations import (
    calculate_personal_arcana,
    zodiac_for_birth_date,
)
from app.whatsapp.repository import whatsapp_repository


SPREAD_OPTIONS = {
    "1": "THREE_CARD_SITUATION",
    "2": "PAST_PRESENT_FUTURE",
    "3": "SELF_OTHER_RELATIONSHIP",
}

YES_ANSWERS = {"yes", "y", "sure", "ok", "okay", "sim", "sí", "si", "s"}
NO_ANSWERS = {"no", "n", "not now", "não", "nao", "ahora no"}
SKIP_ANSWERS = {"skip", "pular", "omitir"}
TAROT_COMMANDS = {"tarot", "/tarot", "reading", "/reading", "leitura", "lectura", "new", "/new"}
PROFILE_COMMANDS = {"profile", "/profile", "perfil", "/perfil"}
HELP_COMMANDS = {"help", "/help", "menu", "/menu", "ajuda", "/ajuda", "ayuda", "/ayuda"}
CANCEL_COMMANDS = {"cancel", "/cancel", "cancelar", "/cancelar"}
LANGUAGE_COMMANDS = {"language", "/language", "idioma", "/idioma"}


def _pick(language: str, en: str, pt: str, es: str) -> str:
    return {"en": en, "pt": pt, "es": es}.get(normalize_language(language), en)


class WhatsAppConversationService:
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

        conversation, conversation_created = whatsapp_repository.get_or_create_conversation_by_number(
            db,
            whatsapp_number=from_number,
            user_id=user.id if user else None,
        )

        if user is None and conversation_created:
            return [language_selection_prompt()]

        if conversation.state in {"AWAITING_LANGUAGE", "AWAITING_LANGUAGE_CHANGE"}:
            selected = parse_language_choice(clean)
            if selected is None:
                return [language_selection_prompt()]
            conversation.language = selected
            if conversation.state == "AWAITING_LANGUAGE":
                conversation.state = "AWAITING_NAME"
                db.commit()
                return [t(selected, "ask_name")]
            self._reset_to_menu(conversation)
            db.commit()
            return [t(selected, "language_changed"), self._main_menu_text(selected)]

        language = normalize_language(conversation.language)

        if user is None and conversation.state == "AWAITING_NAME":
            if len(clean) < 2:
                return [t(language, "ask_name_again")]

            user = user_service.create_named_whatsapp_user(
                db,
                whatsapp_number=from_number,
                name=clean,
            )
            conversation.user_id = user.id
            self._reset_to_menu(conversation)
            db.commit()

            first_name = user.name.split()[0]
            return [t(language, "welcome", name=first_name), self._main_menu_text(language)]

        if user is None:
            conversation.state = "AWAITING_LANGUAGE"
            db.commit()
            return [language_selection_prompt()]

        if command in LANGUAGE_COMMANDS:
            conversation.state = "AWAITING_LANGUAGE_CHANGE"
            conversation.pending_question = None
            conversation.pending_context = None
            db.commit()
            return [language_selection_prompt()]

        if command in CANCEL_COMMANDS:
            self._reset_to_menu(conversation)
            db.commit()
            return [t(language, "cancelled"), self._main_menu_text(language)]

        if command in HELP_COMMANDS:
            return [self._main_menu_text(language)]

        if command in TAROT_COMMANDS:
            conversation.state = "AWAITING_READING_QUESTION"
            conversation.pending_question = None
            conversation.pending_context = None
            db.commit()
            return [self._reading_question_prompt(language)]

        if command in PROFILE_COMMANDS:
            conversation.state = "PROFILE_MENU"
            conversation.pending_question = None
            conversation.pending_context = None
            db.commit()
            return [self._profile_menu_text(language)]

        state = conversation.state

        if state == "PROFILE_MENU":
            if command in {"1", "date", "birth", "birth date", "data", "nascimento", "fecha"}:
                conversation.state = "PROFILE_BIRTH_DATE"
                db.commit()
                return [self._birth_date_prompt(language)]

            if command in {"2", "time", "birth time", "natal chart", "hora", "mapa natal", "carta natal"}:
                if user.profile.birth_date is None:
                    conversation.state = "PROFILE_BIRTH_DATE"
                    db.commit()
                    return [
                        _pick(language,
                              "To calculate your natal chart, I first need your date of birth.",
                              "Para calcular seu mapa natal, primeiro preciso da sua data de nascimento.",
                              "Para calcular tu carta natal, primero necesito tu fecha de nacimiento."),
                        self._birth_date_prompt(language),
                    ]
                conversation.state = "PROFILE_BIRTH_TIME"
                db.commit()
                return [self._birth_time_prompt(language)]

            if command in {"3", "personality", "mbti", "personalidade", "personalidad"}:
                conversation.state = "PROFILE_MBTI_TEST"
                conversation.pending_context = self._encode_mbti_progress(index=0, scores=initial_scores())
                db.commit()
                return [
                    _pick(language,
                          "🧠 Let's take a personality test inspired by the MBTI preference model.\n\nThere are 20 A/B questions. There is no right answer: choose the option that describes you best most of the time.",
                          "🧠 Vamos fazer um teste de personalidade inspirado no modelo de preferências do MBTI.\n\nSão 20 perguntas A/B. Não existe resposta certa: escolha a opção que melhor descreve você na maior parte do tempo.",
                          "🧠 Hagamos un test de personalidad inspirado en el modelo de preferencias MBTI.\n\nSon 20 preguntas A/B. No hay una respuesta correcta: elige la opción que mejor te describa la mayor parte del tiempo."),
                    self._mbti_question(0, language),
                ]

            return [self._profile_menu_text(language)]

        if state == "PROFILE_MBTI_TEST":
            progress = self._decode_mbti_progress(conversation.pending_context)
            index = progress["index"]
            scores = progress["scores"]

            if command not in {"a", "b", "1", "2"}:
                return [
                    _pick(language,
                          "For the personality test, reply only with A or B.",
                          "Para o teste de personalidade, responda apenas A ou B.",
                          "Para el test de personalidad, responde solo A o B."),
                    self._mbti_question(index, language),
                ]

            scores = score_answer(index, command, scores)
            next_index = index + 1

            if next_index < len(MBTI_QUESTIONS):
                conversation.pending_context = self._encode_mbti_progress(index=next_index, scores=scores)
                db.commit()
                return [self._mbti_question(next_index, language)]

            result = calculate_mbti(scores)
            user.profile.mbti = result
            self._reset_to_menu(conversation)
            db.commit()

            description = mbti_description(result, language=language)
            result_text = _pick(
                language,
                f"🧠 Your result is *{result}*.\n\n{description}\n\nThis result describes preference tendencies rather than a rigid category or psychological diagnosis. It has been saved to your profile and can be used as context in future readings.",
                f"🧠 Seu resultado é *{result}*.\n\n{description}\n\nEste resultado descreve tendências de preferência, não uma categoria rígida nem um diagnóstico psicológico. Ele foi salvo no seu perfil e pode ser usado como contexto em leituras futuras.",
                f"🧠 Tu resultado es *{result}*.\n\n{description}\n\nEste resultado describe tendencias de preferencia, no una categoría rígida ni un diagnóstico psicológico. Se guardó en tu perfil y puede usarse como contexto en futuras lecturas.",
            )
            return [result_text, self._main_menu_text(language)]

        if state == "PROFILE_BIRTH_DATE":
            birth_date = self._parse_birth_date(clean)
            if birth_date is None:
                return [self._with_cancel(_pick(language,
                    "I couldn't recognize that date. Send it as DD/MM/YYYY, for example 17/08/2002.",
                    "Não consegui reconhecer essa data. Envie no formato DD/MM/AAAA, por exemplo 17/08/2002.",
                    "No pude reconocer esa fecha. Envíala como DD/MM/AAAA, por ejemplo 17/08/2002."), language)]
            if birth_date > date.today():
                return [self._with_cancel(_pick(language,
                    "Your date of birth cannot be in the future. Please try again.",
                    "Sua data de nascimento não pode estar no futuro. Tente novamente.",
                    "Tu fecha de nacimiento no puede estar en el futuro. Inténtalo de nuevo."), language)]

            zodiac_sign, zodiac_description = zodiac_for_birth_date(birth_date, language=language)
            arcana = calculate_personal_arcana(user.name, birth_date, language=language)

            user.profile.birth_date = birth_date
            user.profile.zodiac_sign = zodiac_sign
            user.profile.sun_sign = zodiac_sign
            user.profile.personal_number = arcana.personal_number
            user.profile.personal_arcana_number = arcana.personal_number
            user.profile.personal_arcana_name = arcana.personal_arcana_name
            user.profile.year_arcana_number = arcana.year_arcana_number
            user.profile.year_arcana_name = arcana.year_arcana_name
            user.profile.year_arcana_reference_year = arcana.reference_year
            conversation.state = "PROFILE_ASK_BIRTH_TIME"
            db.commit()

            personal_caption = _pick(language,
                f"🔮 Your personal number is {arcana.personal_number}.\n\nYour Personal Arcana is {arcana.personal_arcana_name}.\n\n{arcana.personal_arcana_description}",
                f"🔮 Seu número pessoal é {arcana.personal_number}.\n\nSeu Arcano Pessoal é {arcana.personal_arcana_name}.\n\n{arcana.personal_arcana_description}",
                f"🔮 Tu número personal es {arcana.personal_number}.\n\nTu Arcano Personal es {arcana.personal_arcana_name}.\n\n{arcana.personal_arcana_description}")
            year_caption = _pick(language,
                f"✨ Your Year Arcana for {arcana.reference_year} is {arcana.year_arcana_name} ({arcana.year_arcana_number}).\n\n{arcana.year_arcana_description}",
                f"✨ Seu Arcano do Ano para {arcana.reference_year} é {arcana.year_arcana_name} ({arcana.year_arcana_number}).\n\n{arcana.year_arcana_description}",
                f"✨ Tu Arcano del Año para {arcana.reference_year} es {arcana.year_arcana_name} ({arcana.year_arcana_number}).\n\n{arcana.year_arcana_description}")

            return [
                _pick(language,
                      f"Your zodiac sign is {zodiac_sign}.\n\n{zodiac_description}",
                      f"Seu signo é {zodiac_sign}.\n\n{zodiac_description}",
                      f"Tu signo es {zodiac_sign}.\n\n{zodiac_description}"),
                {"type": "image", "url": arcana_image_url(arcana.personal_number), "caption": personal_caption},
                {"type": "image", "url": arcana_image_url(arcana.year_arcana_number), "caption": year_caption},
                self._with_cancel(_pick(language,
                    "If you want, I can calculate the rest of your natal chart. For that I need your birth time and birthplace.\n\nWould you like to provide your birth time now? Reply YES or NO.",
                    "Se quiser, posso calcular o restante do seu mapa natal. Para isso preciso do horário e do local do seu nascimento.\n\nVocê gostaria de informar seu horário de nascimento agora? Responda SIM ou NÃO.",
                    "Si quieres, puedo calcular el resto de tu carta natal. Para eso necesito tu hora y lugar de nacimiento.\n\n¿Quieres indicar tu hora de nacimiento ahora? Responde SÍ o NO."), language),
            ]

        if state == "PROFILE_ASK_BIRTH_TIME":
            if command in YES_ANSWERS:
                conversation.state = "PROFILE_BIRTH_TIME"
                db.commit()
                return [self._birth_time_prompt(language)]
            if command in NO_ANSWERS:
                self._reset_to_menu(conversation)
                db.commit()
                return [_pick(language,
                    "No problem. Use PROFILE whenever you want to complete your natal chart.",
                    "Sem problema. Use PERFIL quando quiser completar seu mapa natal.",
                    "No hay problema. Usa PERFIL cuando quieras completar tu carta natal."), self._main_menu_text(language)]
            return [self._with_cancel(_pick(language,
                "Reply YES to calculate your natal chart now, or NO to leave it for later.",
                "Responda SIM para calcular seu mapa natal agora, ou NÃO para deixar para depois.",
                "Responde SÍ para calcular tu carta natal ahora, o NO para dejarlo para más tarde."), language)]

        if state == "PROFILE_BIRTH_TIME":
            birth_time = self._parse_birth_time(clean)
            if birth_time is None:
                return [self._with_cancel(_pick(language,
                    "I couldn't recognize that time. Send it as HH:MM, for example 14:35.",
                    "Não consegui reconhecer esse horário. Envie no formato HH:MM, por exemplo 14:35.",
                    "No pude reconocer esa hora. Envíala como HH:MM, por ejemplo 14:35."), language)]
            if user.profile.birth_date is None:
                conversation.state = "PROFILE_BIRTH_DATE"
                db.commit()
                return [_pick(language,
                    "I also need your date of birth before calculating the chart.",
                    "Também preciso da sua data de nascimento antes de calcular o mapa.",
                    "También necesito tu fecha de nacimiento antes de calcular la carta."), self._birth_date_prompt(language)]

            user.profile.birth_time = birth_time
            conversation.state = "PROFILE_BIRTH_PLACE"
            db.commit()
            return [self._with_cancel(_pick(language,
                f"Birth time saved: {birth_time.strftime('%H:%M')}.\n\nNow tell me where you were born. Send the city, state/region, and country, for example: Belo Horizonte, Minas Gerais, Brazil.\n\nThe location is needed to determine the timezone and Ascendant.",
                f"Horário de nascimento salvo: {birth_time.strftime('%H:%M')}.\n\nAgora me diga onde você nasceu. Envie cidade, estado/região e país, por exemplo: Belo Horizonte, Minas Gerais, Brasil.\n\nO local é necessário para determinar o fuso horário e o Ascendente.",
                f"Hora de nacimiento guardada: {birth_time.strftime('%H:%M')}.\n\nAhora dime dónde naciste. Envía ciudad, estado/región y país, por ejemplo: Belo Horizonte, Minas Gerais, Brasil.\n\nEl lugar es necesario para determinar la zona horaria y el Ascendente."), language)]

        if state == "PROFILE_BIRTH_PLACE":
            try:
                birth_place = geocode_birth_place(clean, language=language)
                chart = calculate_natal_chart(
                    birth_date=user.profile.birth_date,
                    birth_time=user.profile.birth_time,
                    birth_place=birth_place,
                )
            except (BirthPlaceNotFoundError, BirthTimezoneNotFoundError):
                return [self._with_cancel(_pick(language,
                    "I couldn't locate that place reliably. Try sending it as city, state/region, and country.",
                    "Não consegui localizar esse lugar com segurança. Tente enviar cidade, estado/região e país.",
                    "No pude localizar ese lugar de forma fiable. Intenta enviar ciudad, estado/región y país."), language)]
            except (httpx.HTTPError, ValueError):
                return [self._with_cancel(_pick(language,
                    "I couldn't calculate the natal chart because the location lookup failed. Please try again in a few moments.",
                    "Não consegui calcular o mapa natal porque a busca do local falhou. Tente novamente em alguns instantes.",
                    "No pude calcular la carta natal porque falló la búsqueda del lugar. Inténtalo de nuevo en unos momentos."), language)]

            user.profile.birth_place = birth_place.display_name[:250]
            user.profile.birth_latitude = birth_place.latitude
            user.profile.birth_longitude = birth_place.longitude
            user.profile.birth_timezone = birth_place.timezone
            user.profile.natal_chart = chart
            user.profile.sun_sign = chart["positions"]["Sun"]["sign"]
            user.profile.moon_sign = chart["positions"]["Moon"]["sign"]
            user.profile.rising_sign = chart["ascendant"]["sign"]
            self._reset_to_menu(conversation)
            db.commit()

            return [
                _pick(language,
                      f"Birthplace identified: {birth_place.display_name}.\nTimezone used for the calculation: {birth_place.timezone}.",
                      f"Local de nascimento identificado: {birth_place.display_name}.\nFuso horário usado no cálculo: {birth_place.timezone}.",
                      f"Lugar de nacimiento identificado: {birth_place.display_name}.\nZona horaria utilizada en el cálculo: {birth_place.timezone}."),
                format_natal_chart(chart, language=language),
                self._main_menu_text(language),
            ]

        if state == "AWAITING_READING_QUESTION":
            if not clean:
                return [self._reading_question_prompt(language)]
            conversation.pending_question = clean[:500]
            conversation.pending_context = None
            conversation.state = "AWAITING_CONTEXT"
            db.commit()
            return [self._context_prompt(language)]

        if state == "AWAITING_CONTEXT":
            conversation.pending_context = None if command in SKIP_ANSWERS else clean[:1000]
            conversation.state = "AWAITING_SPREAD"
            db.commit()
            return [self._spread_prompt(language)]

        if state == "AWAITING_SPREAD":
            spread_code = self._parse_spread(clean)
            if spread_code is None:
                return [self._spread_prompt(language)]

            question = conversation.pending_question
            if not question:
                conversation.state = "AWAITING_READING_QUESTION"
                db.commit()
                return [_pick(language,
                    "I lost the pending question.",
                    "Perdi a pergunta que estava pendente.",
                    "Perdí la pregunta que estaba pendiente."), self._reading_question_prompt(language)]

            context = conversation.pending_context
            self._reset_to_menu(conversation)
            db.commit()

            try:
                reading = tarot_reading_flow.create(
                    db=db,
                    user_id=user.id,
                    spread_code=spread_code,
                    question=question,
                    context=context,
                    allow_reversed=True,
                )
            except (AIConfigurationError, AIProviderError):
                return [_pick(language,
                    f"Your cards were drawn and saved, but the AI interpretation failed. This reading can be retried without drawing new cards. Reading ID: {self._latest_failed_reading_id(db, user.id)}",
                    f"Suas cartas foram tiradas e salvas, mas a interpretação da IA falhou. Esta leitura pode ser tentada novamente sem tirar novas cartas. ID da leitura: {self._latest_failed_reading_id(db, user.id)}",
                    f"Tus cartas fueron sacadas y guardadas, pero falló la interpretación de la IA. Esta lectura puede reintentarse sin sacar cartas nuevas. ID de lectura: {self._latest_failed_reading_id(db, user.id)}"), self._main_menu_text(language)]
            except InvalidSpreadError:
                return [t(language, "spread_unavailable"), self._main_menu_text(language)]

            return [*self._format_reading(reading, language), self._main_menu_text(language)]

        self._reset_to_menu(conversation)
        db.commit()
        return [self._main_menu_text(language)]

    @staticmethod
    def _reset_to_menu(conversation) -> None:
        conversation.state = "AWAITING_QUESTION"
        conversation.pending_question = None
        conversation.pending_context = None

    @staticmethod
    def _with_cancel(text: str, language: str) -> str:
        return t(language, "with_cancel", text=text)

    @classmethod
    def _mbti_question(cls, index: int, language: str) -> str:
        return cls._with_cancel(format_question(index, language=language), language)

    @staticmethod
    def _encode_mbti_progress(*, index: int, scores: dict[str, int]) -> str:
        return json.dumps({"index": index, "scores": scores}, separators=(",", ":"))

    @staticmethod
    def _decode_mbti_progress(value: str | None) -> dict:
        try:
            data = json.loads(value or "")
            index = int(data["index"])
            scores = data["scores"]
            if not 0 <= index < len(MBTI_QUESTIONS) or not isinstance(scores, dict):
                raise ValueError
            return {"index": index, "scores": scores}
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            return {"index": 0, "scores": initial_scores()}

    @staticmethod
    def _parse_birth_date(value: str) -> date | None:
        for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
            try:
                return datetime.strptime(value.strip(), fmt).date()
            except ValueError:
                continue
        return None

    @staticmethod
    def _parse_birth_time(value: str):
        try:
            return datetime.strptime(value.strip(), "%H:%M").time()
        except ValueError:
            return None

    @staticmethod
    def _parse_spread(text: str) -> str | None:
        value = text.strip().upper()
        if value in SPREAD_OPTIONS:
            return SPREAD_OPTIONS[value]
        valid_codes = set(SPREAD_OPTIONS.values())
        return value if value in valid_codes else None

    @classmethod
    def _reading_question_prompt(cls, language: str) -> str:
        return cls._with_cancel(t(language, "reading_started"), language)

    @classmethod
    def _context_prompt(cls, language: str) -> str:
        return cls._with_cancel(t(language, "context_prompt"), language)

    @classmethod
    def _birth_date_prompt(cls, language: str) -> str:
        return cls._with_cancel(t(language, "birth_date_prompt"), language)

    @classmethod
    def _birth_time_prompt(cls, language: str) -> str:
        return cls._with_cancel(t(language, "birth_time_prompt"), language)

    @classmethod
    def _profile_menu_text(cls, language: str) -> str:
        return cls._with_cancel(t(language, "profile_menu"), language)

    @classmethod
    def _spread_prompt(cls, language: str) -> str:
        return cls._with_cancel(_pick(language,
            "Choose a spread:\n1 — Current situation / Dynamic / Tendency\n2 — Past / Present / Future\n3 — You / Other person / Relationship\n\nReply with 1, 2, or 3.",
            "Escolha uma tiragem:\n1 — Situação atual / Dinâmica / Tendência\n2 — Passado / Presente / Futuro\n3 — Você / Outra pessoa / Relacionamento\n\nResponda com 1, 2 ou 3.",
            "Elige una tirada:\n1 — Situación actual / Dinámica / Tendencia\n2 — Pasado / Presente / Futuro\n3 — Tú / Otra persona / Relación\n\nResponde con 1, 2 o 3."), language)

    @staticmethod
    def _main_menu_text(language: str = "en") -> str:
        return t(language, "main_menu")

    @staticmethod
    def _latest_failed_reading_id(db: Session, user_id: int) -> str:
        from sqlalchemy import select
        from app.persistence.models import ReadingEntity
        reading_id = db.scalar(
            select(ReadingEntity.id)
            .where(ReadingEntity.user_id == user_id, ReadingEntity.status == "FAILED")
            .order_by(ReadingEntity.id.desc())
            .limit(1)
        )
        return str(reading_id) if reading_id is not None else "unknown"

    @staticmethod
    def _format_reading(reading, language: str) -> list[str]:
        drawn = reading_persistence_service.reconstruct_drawn_cards(reading)
        cards = "\n".join(
            f"{item.position.index}. {item.position.name}: {item.card.name} ({t(language, 'reversed') if item.orientation.value == 'reversed' else t(language, 'upright')})"
            for item in drawn
        )
        return [
            _pick(language, f"Reading #{reading.id}\n\nYour cards:\n{cards}", f"Leitura #{reading.id}\n\nSuas cartas:\n{cards}", f"Lectura #{reading.id}\n\nTus cartas:\n{cards}"),
            f"{t(language, 'overall_label')}\n\n{reading.narrative or ''}",
            f"{t(language, 'cards_label')}\n\n{reading.card_analysis or ''}",
            f"{t(language, 'synthesis_label')}\n\n{reading.synthesis or ''}",
            _pick(language, "Your reading has been saved.", "Sua leitura foi salva.", "Tu lectura ha sido guardada."),
        ]


whatsapp_conversation_service = WhatsAppConversationService()
