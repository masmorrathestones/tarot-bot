from __future__ import annotations

import json

from app.ai.provider import OpenAITextProvider
from app.tarot.mystic_intuition import MysticIntuition
from app.whatsapp.i18n import output_language_instruction


QUESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "question": {"type": "string", "minLength": 8, "maxLength": 220},
    },
    "required": ["question"],
    "additionalProperties": False,
}


class IntuitionConfirmationService:
    def __init__(self) -> None:
        self.provider = OpenAITextProvider()

    def generate_question(
        self,
        *,
        question: str,
        context: str | None,
        profile_snapshot: dict,
        intuition: MysticIntuition,
        language: str,
    ) -> str:
        selected_info = profile_snapshot.get("selected_relevant_information") or []
        natal_chart = profile_snapshot.get("natal_chart") or None

        instructions = (
            "You generate exactly one short yes-or-no confirmation question for a Tarot reading. "
            "The purpose is to test a strong interpretive intuition before the card analysis continues. "
            "The question must feel perceptive and personally connected to the user's actual question/context, but it must remain a question, never a claim of factual psychic knowledge. "
            "It must be SPECIFIC and NON-GENERIC, directly related to the user's situation and to the supplied intuition meaning. "
            "At the same time, do not make it implausibly narrow, over-detailed, or dependent on an invented name/date/event. "
            "Prefer a concrete trait, recurring tension, person/dynamic, hidden practical obstacle, motivation, habit, or contextual feature that the user can simply confirm or deny. "
            "Do not ask something already explicitly stated in the supplied context. Do not ask multiple questions. "
            "Do not mention Tarot cards, alignment names, intuition weights, MBTI, astrology, natal placements, profile databases, or internal mechanisms. "
            "Do not diagnose health or psychiatric conditions and do not invent allegations of crimes, abuse, infidelity, curses, or other high-stakes hidden facts. "
            "Return only the question in the requested language."
        )

        input_text = (
            f"USER QUESTION:\n{question}\n\n"
            f"USER CONTEXT:\n{context or 'None provided'}\n\n"
            f"SELECTED RELEVANT USER INFORMATION:\n{json.dumps(selected_info, ensure_ascii=False)}\n\n"
            f"NATAL CHART:\n{json.dumps(natal_chart, ensure_ascii=False)}\n\n"
            f"STRONG INTUITION INTERPRETIVE MEANING:\n{intuition.description}\n\n"
            f"{output_language_instruction(language)}\n\n"
            "Generate one natural yes-or-no confirmation question. It should sound like a sudden, specific intuition worth checking before continuing."
        )

        payload = self.provider.generate_structured(
            instructions=instructions,
            input_text=input_text,
            schema_name="intuition_confirmation_question",
            schema=QUESTION_SCHEMA,
        )
        result = str(payload.get("question") or "").strip()
        if not result:
            raise ValueError("The AI did not generate an intuition confirmation question.")
        if not result.endswith("?"):
            result += "?"
        return result[:220]


intuition_confirmation_service = IntuitionConfirmationService()
