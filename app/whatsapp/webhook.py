import hashlib
import hmac
import json

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
)
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database.session import SessionLocal, get_db
from app.whatsapp.client import whatsapp_cloud_client
from app.whatsapp.config import get_whatsapp_settings
from app.whatsapp.conversation import whatsapp_conversation_service
from app.whatsapp.repository import whatsapp_repository
from app.whatsapp.schemas import (
    TestWhatsAppMessageRequest,
    TestWhatsAppMessageResponse,
)


router = APIRouter(
    prefix="/api/whatsapp",
    tags=["WhatsApp"],
)


@router.get("/webhook", response_class=PlainTextResponse)
def verify_webhook(
    hub_mode: str | None = Query(default=None, alias="hub.mode"),
    hub_verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    hub_challenge: str | None = Query(default=None, alias="hub.challenge"),
):
    settings = get_whatsapp_settings()

    if (
        hub_mode == "subscribe"
        and settings.verify_token
        and hmac.compare_digest(
            hub_verify_token or "",
            settings.verify_token,
        )
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
    outgoing = whatsapp_conversation_service.handle_text(
        db=db,
        from_number=request.from_number,
        display_name=request.display_name,
        text=request.text,
    )
    return TestWhatsAppMessageResponse(outgoing_messages=outgoing)


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
                "For now I can read text messages only. "
                "Please send your tarot question as text."
            ]
        else:
            outgoing = whatsapp_conversation_service.handle_text(
                db=db,
                from_number=from_number,
                display_name=display_name,
                text=text,
            )

        for message in outgoing:
            sent_messages = _send_outgoing(
                to=from_number,
                message=message,
            )
            for sent in sent_messages:
                whatsapp_repository.register_outbound_message(
                    db,
                    whatsapp_message_id=sent["id"],
                    to_number=from_number,
                    text_body=sent["body"],
                    provider_status=sent.get("status"),
                )

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


def _send_outgoing(*, to: str, message) -> list[dict]:
    if isinstance(message, str):
        return whatsapp_cloud_client.send_text(to=to, body=message)

    if isinstance(message, dict) and message.get("type") == "image":
        return whatsapp_cloud_client.send_image(
            to=to,
            image_url=message["url"],
            caption=message.get("caption") or "",
        )

    raise ValueError(f"Unsupported outgoing WhatsApp message: {message!r}")


def _valid_signature(
    *,
    raw_body: bytes,
    signature: str | None,
    app_secret: str,
) -> bool:
    if not signature or not signature.startswith("sha256="):
        return False

    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


def _extract_messages(payload: dict) -> list[dict]:
    result = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value") or {}
            contacts = value.get("contacts") or []
            contact_names = {
                str(contact.get("wa_id") or ""): (contact.get("profile") or {}).get("name")
                for contact in contacts
            }

            for message in value.get("messages") or []:
                from_number = str(message.get("from") or "")
                if not from_number:
                    continue

                message_type = str(message.get("type") or "unknown")
                text_body = None
                if message_type == "text":
                    text_body = (message.get("text") or {}).get("body")

                result.append(
                    {
                        "message_id": str(message.get("id") or ""),
                        "from_number": from_number,
                        "display_name": contact_names.get(from_number),
                        "message_type": message_type,
                        "text": text_body,
                    }
                )

    return [item for item in result if item["message_id"] and item["from_number"]]


def _extract_statuses(payload: dict) -> list[dict]:
    result = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value") or {}

            for status in value.get("statuses") or []:
                errors = status.get("errors") or []
                first_error = errors[0] if errors else {}
                error_data = first_error.get("error_data") or {}

                result.append(
                    {
                        "whatsapp_message_id": str(status.get("id") or ""),
                        "status": str(status.get("status") or "unknown"),
                        "recipient_id": str(status.get("recipient_id") or "") or None,
                        "error_code": first_error.get("code"),
                        "error_title": first_error.get("title"),
                        "error_message": (
                            first_error.get("message")
                            or error_data.get("details")
                        ),
                    }
                )

    return [item for item in result if item["whatsapp_message_id"]]
