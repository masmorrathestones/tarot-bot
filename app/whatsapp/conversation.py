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

YES_ANSWERS = {"yes", "y", "sure", "ok", "okay"}
NO_ANSWERS = {"no", "n", "not now"}
TAROT_COMMANDS = {"tarot", "/tarot", "reading", "/reading", "new", "/new"}
PROFILE_COMMANDS = {"profile", "/profile"}
HELP_COMMANDS = {"help", "/help", "menu", "/menu"}
CANCEL_COMMANDS = {"cancel", "/cancel"}


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

        conversation, conversation_created = (
            whatsapp_repository.get_or_create_conversation_by_number(
                db,
                whatsapp_number=from_number,
                user_id=user.id if user else None,
            )
        )

        if user is None and conversation_created:
            return [
                "Hi! Before we begin, what would you like me to call you? "
                "Send me your name."
            ]

        if user is None and conversation.state == "AWAITING_NAME":
            if len(clean) < 2:
                return ["Please tell me your name so I can finish setting up your profile."]

            user = user_service.create_named_whatsapp_user(
                db,
                whatsapp_number=from_number,
                name=clean,
            )
            conversation.user_id = user.id
            self._reset_to_menu(conversation)
            db.commit()

            first_name = user.name.split()[0]
            return [
                (
                    f"Hi, {first_name}! Welcome. ✨\n\n"
                    "This is a digital cartomancy experience designed to turn Tarot symbols "
                    "into reflection, interpretation, and narrative."
                ),
                self._main_menu_text(),
            ]

        if user is None:
            conversation.state = "AWAITING_NAME"
            db.commit()
            return ["Before we continue, please tell me your name."]

        # CANCEL is global: it works from every active flow.
        if command in CANCEL_COMMANDS:
            self._reset_to_menu(conversation)
            db.commit()
            return [
                "The current action has been canceled.",
                self._main_menu_text(),
            ]

        if command in HELP_COMMANDS:
            return [self._main_menu_text()]

        if command in TAROT_COMMANDS:
            conversation.state = "AWAITING_READING_QUESTION"
            conversation.pending_question = None
            conversation.pending_context = None
            db.commit()
            return [self._reading_question_prompt()]

        if command in PROFILE_COMMANDS:
            conversation.state = "PROFILE_MENU"
            conversation.pending_question = None
            conversation.pending_context = None
            db.commit()
            return [self._profile_menu_text()]

        state = conversation.state

        if state == "PROFILE_MENU":
            if command in {"1", "date", "birth", "birth date"}:
                conversation.state = "PROFILE_BIRTH_DATE"
                db.commit()
                return [self._birth_date_prompt()]

            if command in {"2", "time", "birth time", "natal chart"}:
                if user.profile.birth_date is None:
                    conversation.state = "PROFILE_BIRTH_DATE"
                    db.commit()
                    return [
                        "To calculate your natal chart, I first need your date of birth.",
                        self._birth_date_prompt(),
                    ]
                conversation.state = "PROFILE_BIRTH_TIME"
                db.commit()
                return [self._birth_time_prompt()]

            if command in {"3", "personality", "mbti"}:
                conversation.state = "PROFILE_MBTI_TEST"
                conversation.pending_context = self._encode_mbti_progress(
                    index=0,
                    scores=initial_scores(),
                )
                db.commit()
                return [
                    (
                        "🧠 Let's take a personality test inspired by the MBTI preference model.\n\n"
                        "There are 20 A/B questions. There is no right answer: choose the option "
                        "that describes you best most of the time."
                    ),
                    self._mbti_question(0),
                ]

            return [self._profile_menu_text()]

        if state == "PROFILE_MBTI_TEST":
            progress = self._decode_mbti_progress(conversation.pending_context)
            index = progress["index"]
            scores = progress["scores"]

            if command not in {"a", "b", "1", "2"}:
                return [
                    "For the personality test, reply only with A or B.",
                    self._mbti_question(index),
                ]

            scores = score_answer(index, command, scores)
            next_index = index + 1

            if next_index < len(MBTI_QUESTIONS):
                conversation.pending_context = self._encode_mbti_progress(
                    index=next_index,
                    scores=scores,
                )
                db.commit()
                return [self._mbti_question(next_index)]

            result = calculate_mbti(scores)
            user.profile.mbti = result
            self._reset_to_menu(conversation)
            db.commit()

            return [
                (
                    f"🧠 Your result is *{result}*.\n\n"
                    f"{mbti_description(result)}\n\n"
                    "This result describes preference tendencies rather than a rigid category "
                    "or psychological diagnosis. It has been saved to your profile and can be "
                    "used as context in future readings."
                ),
                self._main_menu_text(),
            ]

        if state == "PROFILE_BIRTH_DATE":
            birth_date = self._parse_birth_date(clean)
            if birth_date is None:
                return [
                    self._with_cancel(
                        "I couldn't recognize that date. Send it as DD/MM/YYYY, "
                        "for example 17/08/2002."
                    )
                ]
            if birth_date > date.today():
                return [self._with_cancel("Your date of birth cannot be in the future. Please try again.")]

            zodiac_sign, zodiac_description = zodiac_for_birth_date(birth_date)
            arcana = calculate_personal_arcana(user.name, birth_date)

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

            personal_caption = (
                f"🔮 Your personal number is {arcana.personal_number}.\n\n"
                f"Your Personal Arcana is {arcana.personal_arcana_name}.\n\n"
                f"{arcana.personal_arcana_description}"
            )
            year_caption = (
                f"✨ Your Year Arcana for {arcana.reference_year} is "
                f"{arcana.year_arcana_name} ({arcana.year_arcana_number}).\n\n"
                f"{arcana.year_arcana_description}"
            )

            return [
                f"Your zodiac sign is {zodiac_sign}.\n\n{zodiac_description}",
                {
                    "type": "image",
                    "url": arcana_image_url(arcana.personal_number),
                    "caption": personal_caption,
                },
                {
                    "type": "image",
                    "url": arcana_image_url(arcana.year_arcana_number),
                    "caption": year_caption,
                },
                self._with_cancel(
                    "If you want, I can calculate the rest of your natal chart. "
                    "For that I need your birth time and birthplace.\n\n"
                    "Would you like to provide your birth time now? Reply YES or NO."
                ),
            ]

        if state == "PROFILE_ASK_BIRTH_TIME":
            if command in YES_ANSWERS:
                conversation.state = "PROFILE_BIRTH_TIME"
                db.commit()
                return [self._birth_time_prompt()]
            if command in NO_ANSWERS:
                self._reset_to_menu(conversation)
                db.commit()
                return [
                    "No problem. Use PROFILE whenever you want to complete your natal chart.",
                    self._main_menu_text(),
                ]
            return [
                self._with_cancel(
                    "Reply YES to calculate your natal chart now, or NO to leave it for later."
                )
            ]

        if state == "PROFILE_BIRTH_TIME":
            birth_time = self._parse_birth_time(clean)
            if birth_time is None:
                return [
                    self._with_cancel(
                        "I couldn't recognize that time. Send it as HH:MM, "
                        "for example 14:35."
                    )
                ]
            if user.profile.birth_date is None:
                conversation.state = "PROFILE_BIRTH_DATE"
                db.commit()
                return [
                    "I also need your date of birth before calculating the chart.",
                    self._birth_date_prompt(),
                ]

            user.profile.birth_time = birth_time
            conversation.state = "PROFILE_BIRTH_PLACE"
            db.commit()
            return [
                self._with_cancel(
                    f"Birth time saved: {birth_time.strftime('%H:%M')}.\n\n"
                    "Now tell me where you were born. Send the city, state/region, and country, "
                    "for example: Belo Horizonte, Minas Gerais, Brazil.\n\n"
                    "The location is needed to determine the timezone and Ascendant."
                )
            ]

        if state == "PROFILE_BIRTH_PLACE":
            try:
                birth_place = geocode_birth_place(clean)
                chart = calculate_natal_chart(
                    birth_date=user.profile.birth_date,
                    birth_time=user.profile.birth_time,
                    birth_place=birth_place,
                )
            except (BirthPlaceNotFoundError, BirthTimezoneNotFoundError):
                return [
                    self._with_cancel(
                        "I couldn't locate that place reliably. "
                        "Try sending it as city, state/region, and country."
                    )
                ]
            except (httpx.HTTPError, ValueError):
                return [
                    self._with_cancel(
                        "I couldn't calculate the natal chart because the location lookup failed. "
                        "Please try again in a few moments."
                    )
                ]

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
                (
                    f"Birthplace identified: {birth_place.display_name}.\n"
                    f"Timezone used for the calculation: {birth_place.timezone}."
                ),
                format_natal_chart(chart),
                self._main_menu_text(),
            ]

        if state == "AWAITING_READING_QUESTION":
            if not clean:
                return [self._reading_question_prompt()]
            conversation.pending_question = clean[:500]
            conversation.pending_context = None
            conversation.state = "AWAITING_CONTEXT"
            db.commit()
            return [self._context_prompt()]

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
                conversation.state = "AWAITING_READING_QUESTION"
                db.commit()
                return [
                    "I lost the pending question.",
                    self._reading_question_prompt(),
                ]

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
                return [
                    "Your cards were drawn and saved, but the AI interpretation failed. "
                    "This reading can be retried without drawing new cards. "
                    f"Reading ID: {self._latest_failed_reading_id(db, user.id)}",
                    self._main_menu_text(),
                ]
            except InvalidSpreadError:
                return [
                    "That spread is currently unavailable.",
                    self._main_menu_text(),
                ]

            return [*self._format_reading(reading), self._main_menu_text()]

        # Idle/default behavior: arbitrary text never starts a Tarot reading.
        # It simply shows the available actions.
        self._reset_to_menu(conversation)
        db.commit()
        return [self._main_menu_text()]

    @staticmethod
    def _reset_to_menu(conversation) -> None:
        conversation.state = "AWAITING_QUESTION"
        conversation.pending_question = None
        conversation.pending_context = None

    @staticmethod
    def _with_cancel(text: str) -> str:
        return f"{text}\n\nSend CANCEL at any time to return to the main menu."

    @classmethod
    def _mbti_question(cls, index: int) -> str:
        return cls._with_cancel(format_question(index))

    @staticmethod
    def _encode_mbti_progress(*, index: int, scores: dict[str, int]) -> str:
        return json.dumps(
            {"index": index, "scores": scores},
            separators=(",", ":"),
        )

    @staticmethod
    def _decode_mbti_progress(value: str | None) -> dict:
        try:
            data = json.loads(value or "")
            index = int(data["index"])
            scores = data["scores"]
            if not 0 <= index < len(MBTI_QUESTIONS):
                raise ValueError
            if not isinstance(scores, dict):
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
    def _reading_question_prompt(cls) -> str:
        return cls._with_cancel(
            "🔮 Tarot reading started. Send the question you want to explore."
        )

    @classmethod
    def _context_prompt(cls) -> str:
        return cls._with_cancel(
            "Now add any context that may help with the reading, "
            "or reply SKIP if you want to continue with the question alone."
        )

    @classmethod
    def _birth_date_prompt(cls) -> str:
        return cls._with_cancel(
            "What is your date of birth? Send it as DD/MM/YYYY. "
            "Example: 17/08/2002."
        )

    @classmethod
    def _birth_time_prompt(cls) -> str:
        return cls._with_cancel(
            "What is your birth time? Send it as HH:MM. "
            "Example: 14:35."
        )

    @classmethod
    def _profile_menu_text(cls) -> str:
        return cls._with_cancel(
            "You can add or update the following profile information:\n\n"
            "1 — Date of birth\n"
            "2 — Birth time and natal chart\n"
            "3 — Personality test (MBTI)\n\n"
            "Send 1, 2, or 3."
        )

    @classmethod
    def _spread_prompt(cls) -> str:
        return cls._with_cancel(
            "Choose a spread:\n"
            "1 — Current situation / Dynamic / Tendency\n"
            "2 — Past / Present / Future\n"
            "3 — You / Other person / Relationship\n\n"
            "Reply with 1, 2, or 3."
        )

    @staticmethod
    def _main_menu_text() -> str:
        return (
            "What would you like to do?\n\n"
            "TAROT — start a Tarot card reading\n"
            "PROFILE — add or update your personal profile\n"
            "HELP — show this menu again\n\n"
            "A Tarot reading only starts after you send TAROT."
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
            f"Reading #{reading.id}\n\nYour cards:\n{cards}",
            f"Overall narrative\n\n{reading.narrative or ''}",
            f"Card-by-card interpretation\n\n{reading.card_analysis or ''}",
            f"Final synthesis\n\n{reading.synthesis or ''}",
            "Your reading has been saved.",
        ]


whatsapp_conversation_service = WhatsAppConversationService()
