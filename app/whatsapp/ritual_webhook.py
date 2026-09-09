import json

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database.session import SessionLocal, get_db
from app.whatsapp.config import get_whatsapp_settings
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
        if not _valid_signature(
            raw_body=raw_body,
            signature=signature,
            app_secret=settings.app_secret,
        ):
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

    # In the simulator there is no real WhatsApp send boundary, so resolve the
    # deferred action synchronously while preserving the message order.
    expanded: list[str | dict] = []
    for message in outgoing:
        if isinstance(message, dict) and message.get("type") == "deferred_tarot_analysis":
            expanded.extend(
                ritual_whatsapp_conversation_service.complete_analysis(
                    db=db,
                    from_number=request.from_number,
                    reading_id=int(message["reading_id"]),
                )
            )
        else:
            expanded.append(message)

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
            outgoing = [
                "For now I can read text messages only. Please use the menu commands as text."
            ]
        else:
            outgoing = ritual_whatsapp_conversation_service.handle_text(
                db=db,
                from_number=from_number,
                display_name=display_name,
                text=text,
            )

        _dispatch_outgoing(db=db, to=from_number, messages=outgoing)

        whatsapp_repository.mark_event_processed(
            db,
            whatsapp_message_id=whatsapp_message_id,
        )
    except Exception as exc:
        whatsapp_repository.mark_event_failed(
            db,
            whatsapp_message_id=whatsapp_message_id,
            error_message=str(exc),
        )
    finally:
        db.close()


def _dispatch_outgoing(*, db: Session, to: str, messages: list[str | dict]) -> None:
    for message in messages:
        if isinstance(message, dict) and message.get("type") == "deferred_tarot_analysis":
            # Everything before this action has already been sent to WhatsApp.
            # The user therefore sees the complete spread and the "analyzing"
            # message before the blocking AI interpretation request begins.
            follow_up = ritual_whatsapp_conversation_service.complete_analysis(
                db=db,
                from_number=to,
                reading_id=int(message["reading_id"]),
            )
            _dispatch_outgoing(db=db, to=to, messages=follow_up)
            continue

        sent_messages = _send_outgoing(to=to, message=message)
        for sent in sent_messages:
            whatsapp_repository.register_outbound_message(
                db,
                whatsapp_message_id=sent["id"],
                to_number=to,
                text_body=sent["body"],
                provider_status=sent.get("status"),
            )
