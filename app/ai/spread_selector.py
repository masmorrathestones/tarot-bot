import json
from typing import Any

from app.ai.provider import AIProviderError, OpenAITextProvider
from app.database.session import SessionLocal
from app.tarot.spreads import SPREADS
from app.users.relevant_info import relevant_information_service


class SpreadSelectionError(RuntimeError):
    pass


class SpreadSelectionService:
    def __init__(self, provider: OpenAITextProvider | None = None) -> None:
        self._provider = provider

    @property
    def provider(self) -> OpenAITextProvider:
        if self._provider is None:
            self._provider = OpenAITextProvider()
        return self._provider

    def choose_spread(
        self,
        *,
        question: str,
        context: str | None,
        profile_snapshot: dict[str, Any] | None,
    ) -> str:
        available_codes = list(SPREADS.keys())
        if not available_codes:
            raise SpreadSelectionError("No Tarot spreads are configured.")

        catalog = [
            {
                "code": spread.code,
                "name": spread.name,
                "description": spread.description,
                "card_count": len(spread.positions),
                "positions": [
                    {
                        "index": position.index,
                        "name": position.name,
                        "description": position.description,
                    }
                    for position in spread.positions
                ],
            }
            for spread in SPREADS.values()
        ]

        raw_profile = profile_snapshot or {}
        profile = {
            key: value
            for key, value in raw_profile.items()
            if key != "whatsapp_number"
            and value is not None
            and value != ""
            and value != {}
            and value != []
        }

        whatsapp_number = str(raw_profile.get("whatsapp_number") or "").strip()
        user_id: int | None = None
        existing_information: list[dict[str, Any]] = []
        if whatsapp_number:
            db = SessionLocal()
            try:
                user_id, rows = relevant_information_service.list_for_whatsapp(
                    db, whatsapp_number
                )
                existing_information = [
                    {"id": row.id, "text": row.text}
                    for row in rows
                ]
            finally:
                db.close()

        existing_ids = [item["id"] for item in existing_information]
        schema = {
            "type": "object",
            "properties": {
                "spread_code": {"type": "string", "enum": available_codes},
                "new_relevant_information": {
                    "type": ["string", "null"],
                    "description": "At most one very short durable fact explicitly supplied by the user in the current question/context, or null.",
                },
                "selected_relevant_information_ids": {
                    "type": "array",
                    "maxItems": 3,
                    "items": {"type": "integer", "enum": existing_ids} if existing_ids else {"type": "integer"},
                },
            },
            "required": [
                "spread_code",
                "new_relevant_information",
                "selected_relevant_information_ids",
            ],
            "additionalProperties": False,
        }

        instructions = (
            "You perform two tightly scoped tasks. First, select exactly one provided Tarot spread "
            "based on the user's question, optional context, and profile. Second, manage concise "
            "personal context for later interpretation. You may extract at most ONE durable, explicitly "
            "supported user fact from the current question/context. Keep it as short as possible; use null "
            "for transient details, speculation, Tarot conclusions, third-party claims, or anything not useful "
            "for future personalization. If existing relevant-information rows are supplied, choose zero to "
            "three IDs that are genuinely useful for interpreting THIS reading. Do not rewrite or summarize "
            "those rows. The profile and relevant information are secondary context and must not force a spread. "
            "Do not invent facts or return commentary outside the schema."
        )

        input_text = (
            "USER QUESTION:\n"
            f"{question}\n\n"
            "ADDITIONAL CONTEXT:\n"
            f"{context or 'None provided'}\n\n"
            "POPULATED USER PROFILE:\n"
            f"{json.dumps(profile, ensure_ascii=False, default=str, indent=2)}\n\n"
            "EXISTING RELEVANT USER INFORMATION:\n"
            f"{json.dumps(existing_information, ensure_ascii=False, indent=2)}\n\n"
            "AVAILABLE SPREADS:\n"
            f"{json.dumps(catalog, ensure_ascii=False, indent=2)}"
        )

        try:
            result = self.provider.generate_structured(
                instructions=instructions,
                input_text=input_text,
                schema_name="tarot_spread_selection_and_context",
                schema=schema,
            )
        except AIProviderError:
            raise

        spread_code = result.get("spread_code")
        if spread_code not in SPREADS:
            raise SpreadSelectionError(
                "The AI returned a spread outside the configured allow-list."
            )

        if user_id is not None:
            selected_ids = [
                int(value)
                for value in (result.get("selected_relevant_information_ids") or [])[:3]
                if isinstance(value, int) and value in existing_ids
            ]
            new_information = result.get("new_relevant_information")
            db = SessionLocal()
            try:
                relevant_information_service.apply_selection(
                    db,
                    user_id=user_id,
                    selected_ids=selected_ids,
                    new_information=(
                        str(new_information) if new_information is not None else None
                    ),
                )
            finally:
                db.close()

        return str(spread_code)


spread_selection_service = SpreadSelectionService()
