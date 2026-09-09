from sqlalchemy.orm import Session

from app.ai.provider import AIConfigurationError, AIProviderError
from app.tarot.persistence_service import reading_persistence_service
from app.tarot.reading_flow import InvalidSpreadError, tarot_reading_flow
from app.users.service import user_service
from app.whatsapp.repository import whatsapp_repository


ZODIAC_SIGNS = {
    "ARIES": "Aries",
    "TAURUS": "Taurus",
    "GEMINI": "Gemini",
    "CANCER": "Cancer",
    "LEO": "Leo",
    "VIRGO": "Virgo",
    "LIBRA": "Libra",
    "SCORPIO": "Scorpio",
    "SAGITTARIUS": "Sagittarius",
    "CAPRICORN": "Capricorn",
    "AQUARIUS": "Aquarius",
    "PISCES": "Pisces",
}

VALID_MBTI = {
    "ISTJ", "ISFJ", "INFJ", "INTJ",
    "ISTP", "ISFP", "INFP", "INTP",
    "ESTP", "ESFP", "ENFP", "ENTP",
    "ESTJ", "ESFJ", "ENFJ", "ENTJ",
}

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
        user, created = user_service.get_or_create_by_whatsapp(
            db,
            whatsapp_number=from_number,
            display_name=display_name,
        )
        conversation = whatsapp_repository.get_or_create_conversation(
            db,
            user_id=user.id,
        )

        clean = text.strip()
        command = clean.lower()

        if command in {"help", "/help"}:
            return [self._help_text()]

        if command in {"cancel", "/cancel", "new", "/new", "reading"}:
            conversation.state = "AWAITING_QUESTION"
            conversation.pending_question = None
            conversation.pending_context = None
            db.commit()
            return [
                "Ready for a new reading. Send me the question you want to explore."
            ]

        if command in {"profile", "/profile"}:
            conversation.state = "PROFILE_SUN"
            conversation.pending_question = None
            conversation.pending_context = None
            db.commit()
            return [
                "Let's personalize your profile. What is your Sun sign? "
                "Reply with a zodiac sign, or SKIP."
            ]

        if created:
            # The first ordinary message is treated as the reading question,
            # so onboarding does not force extra steps.
            conversation.state = "AWAITING_CONTEXT"
            conversation.pending_question = clean[:500]
            db.commit()
            return [
                f"Welcome, {user.name}. I saved your question.\n\n"
                "Add any context that may help me interpret it, or reply SKIP "
                "if you want the reading based only on the question.\n\n"
                "Tip: you can type PROFILE at any time before a new reading "
                "to add Sun, Moon, Rising and MBTI."
            ]

        state = conversation.state

        if state == "PROFILE_SUN":
            return self._handle_profile_sign(
                db=db,
                user=user,
                conversation=conversation,
                clean=clean,
                field="sun_sign",
                next_state="PROFILE_MOON",
                next_prompt="What is your Moon sign? Reply with a zodiac sign, or SKIP.",
            )

        if state == "PROFILE_MOON":
            return self._handle_profile_sign(
                db=db,
                user=user,
                conversation=conversation,
                clean=clean,
                field="moon_sign",
                next_state="PROFILE_RISING",
                next_prompt="What is your Rising sign? Reply with a zodiac sign, or SKIP.",
            )

        if state == "PROFILE_RISING":
            return self._handle_profile_sign(
                db=db,
                user=user,
                conversation=conversation,
                clean=clean,
                field="rising_sign",
                next_state="PROFILE_MBTI",
                next_prompt="What is your MBTI type? Example: INFJ. Reply SKIP if unknown.",
            )

        if state == "PROFILE_MBTI":
            if command == "skip":
                user.profile.mbti = None
            else:
                mbti = clean.upper()
                if mbti not in VALID_MBTI:
                    return [
                        "I couldn't recognize that MBTI type. "
                        "Send one of the 16 types (for example INTP), or SKIP."
                    ]
                user.profile.mbti = mbti

            conversation.state = "AWAITING_QUESTION"
            db.commit()
            return [
                "Profile saved. Now send me the question you want to explore."
            ]

        if state == "AWAITING_CONTEXT":
            conversation.pending_context = None if command == "skip" else clean[:1000]
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
                return [
                    "I lost the pending question, so I reset the flow. "
                    "Please send your question again."
                ]

            context = conversation.pending_context

            # Reset now so a later provider failure does not leave the chat
            # stuck in AWAITING_SPREAD.
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
            except (AIConfigurationError, AIProviderError) as exc:
                return [
                    "Your cards were drawn and safely saved, but the AI "
                    "interpretation failed. You can retry this reading later. "
                    f"Reading ID: {self._latest_failed_reading_id(db, user.id)}"
                ]
            except InvalidSpreadError:
                return [
                    "That spread is temporarily unavailable. "
                    "Send your question again to start over."
                ]

            return self._format_reading(reading)

        # Default state: treat text as a new question.
        conversation.pending_question = clean[:500]
        conversation.pending_context = None
        conversation.state = "AWAITING_CONTEXT"
        db.commit()

        return [
            "Got it. Now add any context that may help the reading, "
            "or reply SKIP."
        ]

    @staticmethod
    def _handle_profile_sign(
        *,
        db: Session,
        user,
        conversation,
        clean: str,
        field: str,
        next_state: str,
        next_prompt: str,
    ) -> list[str]:
        if clean.lower() == "skip":
            value = None
        else:
            value = ZODIAC_SIGNS.get(clean.upper())
            if value is None:
                return [
                    "I couldn't recognize that zodiac sign. "
                    "Send a sign such as Scorpio or Pisces, or reply SKIP."
                ]

        setattr(user.profile, field, value)
        conversation.state = next_state
        db.commit()
        return [next_prompt]

    @staticmethod
    def _parse_spread(text: str) -> str | None:
        value = text.strip().upper()

        if value in SPREAD_OPTIONS:
            return SPREAD_OPTIONS[value]

        valid_codes = set(SPREAD_OPTIONS.values())
        if value in valid_codes:
            return value

        return None

    @staticmethod
    def _spread_prompt() -> str:
        return (
            "Choose the spread:\n"
            "1 — Current Situation / Dynamic / Tendency\n"
            "2 — Past / Present / Future\n"
            "3 — Self / Other / Relationship\n\n"
            "Reply with 1, 2 or 3."
        )

    @staticmethod
    def _help_text() -> str:
        return (
            "Commands:\n"
            "PROFILE — add or update Sun, Moon, Rising and MBTI\n"
            "NEW — start a new reading\n"
            "CANCEL — cancel the current flow\n"
            "HELP — show this message\n\n"
            "To begin, simply send your tarot question."
        )

    @staticmethod
    def _latest_failed_reading_id(db: Session, user_id: int) -> str:
        # Avoid adding another repository API just for the user-facing error.
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
            (
                f"{item.position.index}. {item.position.name}: "
                f"{item.card.name} ({item.orientation.value.title()})"
            )
            for item in drawn
        )

        return [
            f"Reading #{reading.id}\n\nYour cards:\n{cards}",
            f"Overall narrative\n\n{reading.narrative or ''}",
            f"Card-by-card interpretation\n\n{reading.card_analysis or ''}",
            f"Final synthesis\n\n{reading.synthesis or ''}",
            (
                "Your reading has been saved. "
                "Send another question whenever you want a new reading."
            ),
        ]


whatsapp_conversation_service = WhatsAppConversationService()
