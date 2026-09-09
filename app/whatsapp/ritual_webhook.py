import json
import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database.session import SessionLocal, get_db
from app.whatsapp.config import get_whatsapp_settings
from app.whatsapp.i18n import normalize_language, t
from app.whatsapp.repository import whatsapp_repository
from app.whatsapp.ritual_conversation import ritual_whatsapp_conversation_service
from app.whatsapp.schemas import TestWhatsAppMessageRequest, TestWhatsAppMessageResponse
from app.whatsapp.webhook import (
    _extract_messages,
    _extract_statuses,
    _send_outgoing,
    _valid_signature,
)


router = APIRouter(prefix="/api/whatsapp", tags=["WhatsApp"])

CARD_SEND_INTERVAL_SECONDS = 3
AFTER_LAST_CARD_BEFORE_ANALYSIS_SECONDS = 10.0
AFTER_OVERALL_NARRATIVE_SECONDS = 10.0
FINAL_SYNTHESIS_DELAY_SECONDS = 12.0
NARRATIVE_CAPTION_MAX_CHARS = 700


@router.get("/webhook", response_class=PlainTextResponse)
def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    settings = get_whatsapp_settings()
    import hmac

    if (
        hub_mode == "subscribe"
        and settings.verify_token
        and hmac.compare_digest(hub_verify_token or "", settings.verify_token)
    ):
        return PlainTextResponse(content=hub_challenge or "", status_code=200)

    raise HTTPException(status_code=403, detail="Webhook verification failed.")


@router.post("/webhook")
async def receive_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    raw_body = await request.body()
    settings = get_whatsapp_settings()

    if settings.app_secret:
        signature = request.headers.get("X-Hub-Signature-256")
        if not _valid_signature(raw_body=raw_body, signature=signature, app_secret=settings.app_secret):
            raise HTTPException(status_code=401, detail="Invalid webhook signature.")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload.") from exc

    for status in _extract_statuses(payload):
        whatsapp_repository.update_outbound_status(db, **status)

    for item in _extract_messages(payload):
        is_new = whatsapp_repository.register_inbound_event(
            db,
            whatsapp_message_id=item["message_id"],
            from_number=item["from_number"],
            display_name=item["display_name"],
            message_type=item["message_type"],
            text_body=item["text"],
        )
        if not is_new:
            continue

        background_tasks.add_task(
            _process_registered_message,
            whatsapp_message_id=item["message_id"],
            from_number=item["from_number"],
            display_name=item["display_name"],
            message_type=item["message_type"],
            text=item["text"],
        )

    return {"status": "accepted"}


@router.post("/test-message", response_model=TestWhatsAppMessageResponse)
def simulate_text_message(
    request: TestWhatsAppMessageRequest,
    db: Session = Depends(get_db),
):
    outgoing = ritual_whatsapp_conversation_service.handle_text(
        db=db,
        from_number=request.from_number,
        display_name=request.display_name,
        text=request.text,
    )

    expanded: list[str | dict] = []
    pending_spread_image: dict | None = None

    for message in outgoing:
        if _is_complete_spread_image(message):
            pending_spread_image = dict(message)
            continue

        if _is_analysis_wait_message(message):
            expanded.append(t(str(message.get("language") or "en"), "analysis_wait"))
            continue

        if isinstance(message, dict) and message.get("type") == "deferred_tarot_analysis":
            follow_up = ritual_whatsapp_conversation_service.complete_analysis(
                db=db,
                from_number=request.from_number,
                reading_id=int(message["reading_id"]),
            )
            spread_message, remaining = _combine_spread_with_narrative(pending_spread_image, follow_up)
            if spread_message is not None:
                expanded.append(spread_message)
            expanded.extend(remaining)
            pending_spread_image = None
            continue

        expanded.append(message)

    if pending_spread_image is not None:
        expanded.append(pending_spread_image)

    return TestWhatsAppMessageResponse(outgoing_messages=expanded)


def _process_registered_message(
    *,
    whatsapp_message_id: str,
    from_number: str,
    display_name: str | None,
    message_type: str,
    text: str | None,
) -> None:
    db = SessionLocal()

    try:
        if message_type != "text" or not text:
            language = _conversation_language(db, from_number)
            outgoing = [{
                "en": "For now I can read text messages only. Please use the menu commands as text.",
                "pt": "Por enquanto, só consigo ler mensagens de texto. Use os comandos do menu em texto.",
                "es": "Por ahora, solo puedo leer mensajes de texto. Usa los comandos del menú como texto.",
            }[language]]
        else:
            outgoing = ritual_whatsapp_conversation_service.handle_text(
                db=db,
                from_number=from_number,
                display_name=display_name,
                text=text,
            )

        _dispatch_outgoing(db=db, to=from_number, messages=outgoing)
        whatsapp_repository.mark_event_processed(db, whatsapp_message_id=whatsapp_message_id)
    except Exception as exc:
        whatsapp_repository.mark_event_failed(
            db,
            whatsapp_message_id=whatsapp_message_id,
            error_message=str(exc),
        )
    finally:
        db.close()


def _conversation_language(db: Session, to: str) -> str:
    conversation, _ = whatsapp_repository.get_or_create_conversation_by_number(
        db,
        whatsapp_number=to,
    )
    return normalize_language(conversation.language)


def _dispatch_outgoing(*, db: Session, to: str, messages: list[str | dict]) -> None:
    pending_spread_image: dict | None = None

    for message in messages:
        if _is_complete_spread_image(message):
            pending_spread_image = dict(message)
            continue

        if _is_analysis_wait_message(message):
            time.sleep(AFTER_LAST_CARD_BEFORE_ANALYSIS_SECONDS)
            language = normalize_language(str(message.get("language") or _conversation_language(db, to)))
            _send_and_record(db=db, to=to, message=t(language, "analysis_wait"))
            continue

        if isinstance(message, dict) and message.get("type") == "deferred_tarot_analysis":
            follow_up = ritual_whatsapp_conversation_service.complete_analysis(
                db=db,
                from_number=to,
                reading_id=int(message["reading_id"]),
            )
            spread_message, remaining = _combine_spread_with_narrative(pending_spread_image, follow_up)
            _dispatch_analysis_results(
                db=db,
                to=to,
                spread_message=spread_message,
                remaining=remaining,
            )
            pending_spread_image = None
            continue

        _send_and_record(db=db, to=to, message=message)
        if _is_individual_card_image(message):
            time.sleep(CARD_SEND_INTERVAL_SECONDS)

    if pending_spread_image is not None:
        _send_and_record(db=db, to=to, message=pending_spread_image)


def _dispatch_analysis_results(
    *,
    db: Session,
    to: str,
    spread_message: dict | None,
    remaining: list[str | dict],
) -> None:
    if spread_message is not None:
        _send_and_record(db=db, to=to, message=spread_message)
        time.sleep(AFTER_OVERALL_NARRATIVE_SECONDS)

    final_synthesis: str | dict | None = None
    trailing_messages: list[str | dict] = []

    for message in remaining:
        if _is_final_synthesis_message(message):
            final_synthesis = message
            continue

        if final_synthesis is None:
            _send_and_record(db=db, to=to, message=message)
        else:
            trailing_messages.append(message)

    if final_synthesis is not None:
        time.sleep(FINAL_SYNTHESIS_DELAY_SECONDS)
        _send_and_record(db=db, to=to, message=final_synthesis)

    for message in trailing_messages:
        _send_and_record(db=db, to=to, message=message)


def _send_and_record(*, db: Session, to: str, message: str | dict) -> None:
    sent_messages = _send_outgoing(to=to, message=message)
    for sent in sent_messages:
        whatsapp_repository.register_outbound_message(
            db,
            whatsapp_message_id=sent["id"],
            to_number=to,
            text_body=sent["body"],
            provider_status=sent.get("status"),
        )


def _is_analysis_wait_message(message: str | dict) -> bool:
    return isinstance(message, dict) and message.get("type") == "analysis_wait"


def _is_final_synthesis_message(message: str | dict) -> bool:
    if not isinstance(message, str):
        return False
    return message.startswith(("*Final synthesis*", "*Síntese final*", "*Síntesis final*"))


def _is_individual_card_image(message: str | dict) -> bool:
    return (
        isinstance(message, dict)
        and message.get("type") == "image"
        and "/api/assets/cards/" in str(message.get("url") or "")
    )


def _is_complete_spread_image(message: str | dict) -> bool:
    return (
        isinstance(message, dict)
        and message.get("type") == "image"
        and "/api/assets/readings/" in str(message.get("url") or "")
        and str(message.get("url") or "").endswith("/spread.jpg")
    )


def _combine_spread_with_narrative(
    spread_image: dict | None,
    follow_up: list[str | dict],
) -> tuple[dict | None, list[str | dict]]:
    if spread_image is None:
        return None, follow_up

    remaining = list(follow_up)
    narrative: str | None = None
    label: str | None = None

    if remaining and isinstance(remaining[0], str):
        first = remaining[0]
        for candidate in ("Overall narrative", "Narrativa geral", "Narrativa general"):
            prefix = f"*{candidate}*\n\n"
            if first.startswith(prefix):
                narrative = first[len(prefix):].strip()
                label = candidate
                remaining = remaining[1:]
                break

    combined = dict(spread_image)
    if narrative:
        compact = _compact_text(narrative, NARRATIVE_CAPTION_MAX_CHARS)
        combined["caption"] = f"*{label or 'Overall narrative'}*\n\n{compact}"

    return combined, remaining


def _compact_text(text: str, max_chars: int) -> str:
    clean = " ".join(text.split())
    if len(clean) <= max_chars:
        return clean

    cutoff = clean[: max_chars + 1]
    sentence_end = max(cutoff.rfind(". "), cutoff.rfind("! "), cutoff.rfind("? "))
    if sentence_end >= int(max_chars * 0.6):
        return cutoff[: sentence_end + 1].strip()

    word_end = cutoff.rfind(" ")
    if word_end > 0:
        cutoff = cutoff[:word_end]
    return cutoff.rstrip(" ,;:-") + "…"
