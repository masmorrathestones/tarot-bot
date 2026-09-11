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
            "The purpose is NOT to restate, paraphrase, narrow, or answer the user's original question. "
            "The purpose is to test a strong interpretive intuition by asking about a DIFFERENT but relevant fact, pattern, history, dynamic, tendency, or circumstance that could help explain or contextualize the reading. "

            "Treat the user's question and context as the topic boundary, not as the content of the confirmation question. "
            "The confirmation question must EXPAND the context sideways or backwards, rather than asking again about the same future event or outcome the user wants to know about. "

            "IMPORTANT: Never convert the user's original question into a yes-or-no form. "
            "Never ask whether the predicted event, outcome, possibility, or intuition itself is going to happen. "
            "Never merely add an adjective or interpretation to the user's question and ask whether that is true. "

            "Instead, infer what kind of adjacent information would be most diagnostic for the supplied intuition. "
            "Good targets include: recurring patterns in past relationships, habitual reactions, unresolved tensions, relationship dynamics, recent changes, fears, expectations, interpersonal styles, practical obstacles, or background circumstances. "
            "Prefer asking about something the user can recognize from their lived experience, especially something from the recent past or present that would meaningfully strengthen or weaken the intuition. "

            "A good question should make the user think: 'interesting, why did it ask me that?', while still clearly relating to the subject they brought up. "
            "It should reveal NEW information that was not already supplied. "

            "Example of BAD behavior: "
            "User asks 'How will my love life be at the end of this year and next year?' "
            "Bad question: 'Do you feel an intense attraction may bring instability or conflict at the end of this year or next year?' "
            "This is bad because it simply rewrites the user's original future-oriented question using the intuition. "

            "Example of GOOD behavior: "
            "User asks 'How will my love life be at the end of this year and next year?' "
            "Strong intuition suggests instability or chaotic emotional dynamics. "
            "Good question: 'Have your most recent romantic relationships tended to be unstable or difficult to sustain?' "
            "This is good because it explores a related historical pattern that can confirm or weaken the intuition without repeating the original question. "

            "The question must feel perceptive and personally connected to the user's actual situation, but it must remain a question, never a claim of factual psychic knowledge. "
            "It must be SPECIFIC and NON-GENERIC, but not implausibly narrow or dependent on invented names, dates, events, or facts. "
            "Do not ask something already explicitly stated in the supplied context. "
            "Do not ask multiple questions. "

            "Do not mention Tarot cards, alignment names, intuition weights, MBTI, astrology, natal placements, profile databases, or internal mechanisms. "
            "Do not diagnose health or psychiatric conditions and do not invent allegations of crimes, abuse, infidelity, curses, or other high-stakes hidden facts. "

            "Before writing the final question, silently check: "
            "1) Am I asking for genuinely new contextual information? "
            "2) Would the answer help confirm or weaken the intuition? "
            "3) Is this substantially different from the user's original question? "
            "If any answer is no, generate a different question. "

            "Return only the question in the requested language."
        )

        input_text = (
            f"USER QUESTION:\n{question}\n\n"
            f"USER CONTEXT:\n{context or 'None provided'}\n\n"
            f"SELECTED RELEVANT USER INFORMATION:\n{json.dumps(selected_info, ensure_ascii=False)}\n\n"
            f"NATAL CHART:\n{json.dumps(natal_chart, ensure_ascii=False)}\n\n"
            f"STRONG INTUITION INTERPRETIVE MEANING:\n{intuition.description}\n\n"
            f"{output_language_instruction(language)}\n\n"
            "Generate one natural yes-or-no confirmation question that uncovers NEW adjacent context. "
            "Do not ask about the same outcome the user originally asked about. "
            "Use the intuition to decide what hidden pattern, past experience, present dynamic, or background circumstance would be most useful to verify.")

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
