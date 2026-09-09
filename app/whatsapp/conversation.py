from datetime import date, datetime

from sqlalchemy.orm import Session

from app.ai.provider import AIConfigurationError, AIProviderError
from app.tarot.persistence_service import reading_persistence_service
from app.tarot.reading_flow import InvalidSpreadError, tarot_reading_flow
from app.users.service import UserNotFoundError, user_service
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


class WhatsAppConversationService:
    def handle_text(
        self,
        *,
        db: Session,
        from_number: str,
        display_name: str | None,
        text: str,
    ) -> list[str]:
        clean = text.strip()
        command = clean.lower()

        try:
            user = user_service.get_by_whatsapp(db, from_number)
        except UserNotFoundError:
            user = None

        conversation, conversation_created = (
            whatsapp_repository.get_or_create_conversation_by_number(
                db,
                whatsapp_number=from_number,
                user_id=user.id if user else None,
            )
        )

        # A brand-new number starts with a name prompt. The first message is
        # only the contact trigger; it is not silently used as the user's name.
        if user is None and conversation_created:
            return [
                "Olá! Antes de começarmos, como você gostaria de ser chamado? "
                "Pode me enviar seu nome."
            ]

        if user is None and conversation.state == "AWAITING_NAME":
            if len(clean) < 2:
                return ["Me diga seu nome para eu concluir seu cadastro."]

            user = user_service.create_named_whatsapp_user(
                db,
                whatsapp_number=from_number,
                name=clean,
            )
            conversation.user_id = user.id
            conversation.state = "AWAITING_QUESTION"
            db.commit()

            first_name = user.name.split()[0]
            return [
                (
                    f"Olá, {first_name}! Seja bem-vindo. ✨\n\n"
                    "Lorem ipsum dolor sit amet, consectetur adipiscing elit. "
                    "Esta é uma experiência de cartomancia digital pensada para "
                    "transformar símbolos do Tarô em reflexão e narrativa."
                ),
                self._help_text(),
            ]

        if user is None:
            # Defensive recovery for an inconsistent onboarding row.
            conversation.state = "AWAITING_NAME"
            db.commit()
            return ["Antes de continuarmos, me diga seu nome."]

        if command in {"ajuda", "help", "/help", "/ajuda"}:
            return [self._help_text()]

        if command in {"cancelar", "cancel", "/cancel", "/cancelar"}:
            conversation.state = "AWAITING_QUESTION"
            conversation.pending_question = None
            conversation.pending_context = None
            db.commit()
            return ["Fluxo atual cancelado. Quando quiser, envie uma nova pergunta."]

        if command in {"nova", "new", "/new", "/nova", "leitura", "reading"}:
            conversation.state = "AWAITING_QUESTION"
            conversation.pending_question = None
            conversation.pending_context = None
            db.commit()
            return ["Pronto para uma nova leitura. Envie a pergunta que você quer explorar."]

        if command in {"perfil", "profile", "/profile", "/perfil"}:
            conversation.state = "PROFILE_MENU"
            conversation.pending_question = None
            conversation.pending_context = None
            db.commit()
            return [self._profile_menu_text()]

        state = conversation.state

        if state == "PROFILE_MENU":
            if command in {"1", "data", "nascimento", "data de nascimento"}:
                conversation.state = "PROFILE_BIRTH_DATE"
                db.commit()
                return [
                    "Qual é sua data de nascimento? Envie no formato DD/MM/AAAA. "
                    "Exemplo: 17/08/2002."
                ]
            if command in {"2", "hora", "horário", "hora de nascimento"}:
                conversation.state = "PROFILE_BIRTH_TIME"
                db.commit()
                return [
                    "Qual é sua hora de nascimento? Envie no formato HH:MM. "
                    "Exemplo: 14:35."
                ]
            if command in {"3", "personalidade"}:
                return [
                    "O cadastro de personalidade ainda está sendo preparado. "
                    "Por enquanto você pode cadastrar sua data ou hora de nascimento.",
                    self._profile_menu_text(),
                ]
            return [self._profile_menu_text()]

        if state == "PROFILE_BIRTH_DATE":
            birth_date = self._parse_birth_date(clean)
            if birth_date is None:
                return [
                    "Não consegui reconhecer essa data. Envie no formato DD/MM/AAAA, "
                    "por exemplo 17/08/2002."
                ]
            if birth_date > date.today():
                return ["A data de nascimento não pode estar no futuro. Tente novamente."]

            zodiac_sign, zodiac_description = zodiac_for_birth_date(birth_date)
            arcana = calculate_personal_arcana(user.name, birth_date)

            user.profile.birth_date = birth_date
            user.profile.zodiac_sign = zodiac_sign
            # Keep the existing sun_sign field in sync for the AI profile layer.
            user.profile.sun_sign = zodiac_sign
            user.profile.personal_number = arcana.personal_number
            user.profile.personal_arcana_number = arcana.personal_number
            user.profile.personal_arcana_name = arcana.personal_arcana_name
            user.profile.year_arcana_number = arcana.year_arcana_number
            user.profile.year_arcana_name = arcana.year_arcana_name
            user.profile.year_arcana_reference_year = arcana.reference_year
            conversation.state = "AWAITING_QUESTION"
            db.commit()

            return [
                f"♈ Seu signo é {zodiac_sign}.\n\n{zodiac_description}",
                (
                    f"🔮 Com base no seu nome e na sua data de nascimento, "
                    f"seu número pessoal é {arcana.personal_number}.\n\n"
                    f"Seu Arcano Pessoal é {arcana.personal_arcana_name}.\n"
                    f"{arcana.personal_arcana_description}\n\n"
                    f"Para {arcana.reference_year}, seu Arcano do Ano é "
                    f"{arcana.year_arcana_name} ({arcana.year_arcana_number}).\n"
                    f"{arcana.year_arcana_description}"
                ),
            ]

        if state == "PROFILE_BIRTH_TIME":
            birth_time = self._parse_birth_time(clean)
            if birth_time is None:
                return [
                    "Não consegui reconhecer esse horário. Envie no formato HH:MM, "
                    "por exemplo 14:35."
                ]
            user.profile.birth_time = birth_time
            conversation.state = "AWAITING_QUESTION"
            db.commit()
            return [
                f"Hora de nascimento salva: {birth_time.strftime('%H:%M')}."
            ]

        if state == "AWAITING_CONTEXT":
            conversation.pending_context = None if command in {"skip", "pular"} else clean[:1000]
            conversation.state = "AWAITING_SPREAD"
            db.commit()
            return [self._spread_prompt()]

        if state == "AWAITING_SPREAD":
            spread_code = self._parse_spread(clean)
            if spread_code is None:
                return [self._spread_prompt()]

            question = conversation.pending_question
            if not question:
                conversation.state = "AWAITING_QUESTION"
                db.commit()
                return ["Perdi a pergunta pendente. Envie sua pergunta novamente."]

            context = conversation.pending_context
            conversation.state = "AWAITING_QUESTION"
            conversation.pending_question = None
            conversation.pending_context = None
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
                return [
                    "Suas cartas foram sorteadas e salvas, mas a interpretação da IA "
                    "falhou. Esta leitura poderá ser repetida sem sortear novas cartas. "
                    f"ID da leitura: {self._latest_failed_reading_id(db, user.id)}"
                ]
            except InvalidSpreadError:
                return ["Essa tiragem está indisponível no momento. Envie sua pergunta novamente."]

            return self._format_reading(reading)

        # Default READY state: ordinary text starts a reading.
        conversation.pending_question = clean[:500]
        conversation.pending_context = None
        conversation.state = "AWAITING_CONTEXT"
        db.commit()
        return [
            "Entendi. Agora acrescente qualquer contexto que possa ajudar na leitura, "
            "ou responda PULAR se quiser seguir apenas com a pergunta."
        ]

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

    @staticmethod
    def _profile_menu_text() -> str:
        return (
            "Você pode complementar seu perfil com:\n\n"
            "1 — Data de nascimento\n"
            "2 — Hora de nascimento\n"
            "3 — Personalidade (em breve)\n\n"
            "Envie o número da informação que deseja cadastrar."
        )

    @staticmethod
    def _spread_prompt() -> str:
        return (
            "Escolha a tiragem:\n"
            "1 — Situação atual / Dinâmica / Tendência\n"
            "2 — Passado / Presente / Futuro\n"
            "3 — Você / Outra pessoa / Relação\n\n"
            "Responda com 1, 2 ou 3."
        )

    @staticmethod
    def _help_text() -> str:
        return (
            "Comandos disponíveis:\n\n"
            "PERFIL — cadastrar ou atualizar informações pessoais\n"
            "NOVA — iniciar uma nova leitura\n"
            "CANCELAR — cancelar o fluxo atual\n"
            "AJUDA — mostrar estes comandos\n\n"
            "Para começar uma leitura, basta enviar sua pergunta."
        )

    @staticmethod
    def _latest_failed_reading_id(db: Session, user_id: int) -> str:
        from sqlalchemy import select
        from app.persistence.models import ReadingEntity

        reading_id = db.scalar(
            select(ReadingEntity.id)
            .where(
                ReadingEntity.user_id == user_id,
                ReadingEntity.status == "FAILED",
            )
            .order_by(ReadingEntity.id.desc())
            .limit(1)
        )
        return str(reading_id) if reading_id is not None else "unknown"

    @staticmethod
    def _format_reading(reading) -> list[str]:
        drawn = reading_persistence_service.reconstruct_drawn_cards(reading)
        cards = "\n".join(
            f"{item.position.index}. {item.position.name}: {item.card.name} ({item.orientation.value.title()})"
            for item in drawn
        )
        return [
            f"Leitura #{reading.id}\n\nSuas cartas:\n{cards}",
            f"Narrativa geral\n\n{reading.narrative or ''}",
            f"Interpretação carta a carta\n\n{reading.card_analysis or ''}",
            f"Síntese final\n\n{reading.synthesis or ''}",
            "Sua leitura foi salva. Envie outra pergunta quando quiser começar uma nova.",
        ]


whatsapp_conversation_service = WhatsAppConversationService()
