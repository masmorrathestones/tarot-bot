from __future__ import annotations

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.payments.config import get_payment_settings
from app.payments.service import tarot_payment_service
from app.whatsapp.ritual_conversation import ritual_whatsapp_conversation_service


router = APIRouter(prefix="/api/payments", tags=["Payments"])


@router.get("/success", response_class=HTMLResponse)
def payment_success() -> str:
    return (
        "<html><body style='font-family:sans-serif;text-align:center;padding:40px'>"
        "<h2>Payment confirmed</h2>"
        "<p>You can return to WhatsApp. Your Tarot reading will continue there automatically.</p>"
        "</body></html>"
    )


@router.get("/cancelled", response_class=HTMLResponse)
def payment_cancelled() -> str:
    return (
        "<html><body style='font-family:sans-serif;text-align:center;padding:40px'>"
        "<h2>Payment not completed</h2>"
        "<p>You can return to WhatsApp. The reading will not proceed unless payment is completed.</p>"
        "</body></html>"
    )


@router.post("/stripe/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    settings = get_payment_settings()
    if not settings.stripe_webhook_secret:
        raise HTTPException(status_code=503, detail="Stripe webhook is not configured.")

    payload = await request.body()
    signature = request.headers.get("stripe-signature")
    if not signature:
        raise HTTPException(status_code=400, detail="Missing Stripe signature.")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=signature,
            secret=settings.stripe_webhook_secret,
        )
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(status_code=400, detail="Invalid Stripe webhook.") from exc

    # stripe-python returns a Stripe Event object, not a plain dict.
    # Convert it before using dict methods such as .get().
    event_data = event.to_dict()
    event_type = event_data.get("type")
    session = (event_data.get("data") or {}).get("object") or {}
    session_id = str(session.get("id") or "")
    if not session_id:
        return {"status": "ignored"}

    if event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
        if event_type == "checkout.session.completed" and session.get("payment_status") != "paid":
            return {"status": "awaiting_payment"}

        payment, changed = tarot_payment_service.mark_paid(
            db=db,
            provider_session_id=session_id,
        )
        if payment is None or not changed:
            return {"status": "already_processed"}

        to_number, messages = ritual_whatsapp_conversation_service.resume_after_payment(
            db=db,
            conversation_id=payment.conversation_id,
            provider_session_id=session_id,
        )
        if to_number and messages:
            # Local import avoids coupling the payment service to WhatsApp routing.
            from app.whatsapp.ritual_webhook import _dispatch_outgoing

            _dispatch_outgoing(db=db, to=to_number, messages=messages)
        return {"status": "paid"}

    if event_type == "checkout.session.expired":
        payment, changed = tarot_payment_service.mark_expired(
            db=db,
            provider_session_id=session_id,
        )
        if payment is None or not changed:
            return {"status": "already_processed"}

        to_number, messages = ritual_whatsapp_conversation_service.cancel_unpaid_payment(
            db=db,
            conversation_id=payment.conversation_id,
            provider_session_id=session_id,
        )
        if to_number and messages:
            from app.whatsapp.ritual_webhook import _dispatch_outgoing

            _dispatch_outgoing(db=db, to=to_number, messages=messages)
        return {"status": "expired"}

    return {"status": "ignored"}
