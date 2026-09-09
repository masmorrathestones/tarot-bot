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
from app.whatsapp.client import (
    WhatsAppConfigurationError,
    WhatsAppProviderError,
    whatsapp_cloud_client,
)
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
    hub_verify_token: str | None = Query(
        default=None,
        alias="hub.verify_token",
    ),
    hub_challenge: str | None = Query(
        default=None,
        alias="hub.challenge",
    ),
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
        return PlainTextResponse(
            content=hub_challenge or "",
            status_code=200,
        )

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

    inbound_messages = _extract_messages(payload)

    for item in inbound_messages:
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

    # Meta should receive an acknowledgement quickly. AI work runs after this.
    return {"status": "accepted"}


@router.post(
    "/test-message",
    response_model=TestWhatsAppMessageResponse,
)
def simulate_text_message(
    request: TestWhatsAppMessageRequest,
    db: Session = Depends(get_db),
):
    """
    Local/dev-only conversational simulator.

    It exercises user creation, conversation state, profile onboarding,
    reading persistence and the AI service without requiring Meta credentials.
    """
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
            whatsapp_cloud_client.send_text(
                to=from_number,
                body=(
                    "For now I can read text messages only. "
                    "Please send your tarot question as text."
                ),
            )
            whatsapp_repository.mark_event_processed(
                db,
                whatsapp_message_id=whatsapp_message_id,
            )
            return

        outgoing = whatsapp_conversation_service.handle_text(
            db=db,
            from_number=from_number,
            display_name=display_name,
            text=text,
        )

        for message in outgoing:
            whatsapp_cloud_client.send_text(
                to=from_number,
                body=message,
            )

        whatsapp_repository.mark_event_processed(
            db,
            whatsapp_message_id=whatsapp_message_id,
        )
    except Exception as exc:
        # The broad catch is intentional at the background-worker boundary:
        # webhook processing must be observable instead of silently dying.
        try:
            whatsapp_repository.mark_event_failed(
                db,
                whatsapp_message_id=whatsapp_message_id,
                error_message=str(exc),
            )
        finally:
            db.close()
        return
    finally:
        if db.is_active:
            db.close()


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
            contact_names = {}

            for contact in contacts:
                wa_id = str(contact.get("wa_id") or "")
                name = (contact.get("profile") or {}).get("name")
                if wa_id:
                    contact_names[wa_id] = name

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

    return [
        item
        for item in result
        if item["message_id"] and item["from_number"]
    ]
