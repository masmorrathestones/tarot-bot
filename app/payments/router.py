from __future__ import annotations

import html

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.payments.config import get_payment_settings
from app.payments.service import (
    PaymentConfigurationError,
    PaymentProviderError,
    tarot_payment_service,
)
from app.persistence.models import WhatsAppConversationEntity
from app.plans.router import handle_plan_stripe_event
from app.whatsapp.i18n import normalize_language
from app.whatsapp.ritual_conversation import ritual_whatsapp_conversation_service
from app.whatsapp.ritual_state import whatsapp_tarot_flow_store


router = APIRouter(prefix="/api/payments", tags=["Payments"])


def _money(currency: str, amount_cents: int) -> str:
    amount = amount_cents / 100
    if currency == "brl":
        return f"R$ {amount:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"US$ {amount:.2f}"


def _payment_language(db: Session, conversation_id: int) -> str:
    conversation = db.get(WhatsAppConversationEntity, conversation_id)
    return normalize_language(conversation.language if conversation else "en")


def _choice_html(*, token: str, language: str) -> str:
    settings = get_payment_settings()
    usd = _money("usd", settings.usd_amount_cents)
    brl = _money("brl", settings.brl_amount_cents)
    labels = {
        "en": {
            "title": "Choose payment currency",
            "subtitle": "Select how you want to pay for this Tarot reading.",
            "usd": f"Pay in US dollars — {usd}",
            "brl": f"Pay in Brazilian reais — {brl}",
            "note": "You will be redirected to Stripe's secure checkout.",
        },
        "pt": {
            "title": "Escolha a moeda do pagamento",
            "subtitle": "Selecione como você quer pagar por esta leitura de Tarô.",
            "usd": f"Pagar em dólar — {usd}",
            "brl": f"Pagar em reais — {brl}",
            "note": "Você será redirecionado para o checkout seguro da Stripe.",
        },
        "es": {
            "title": "Elige la moneda del pago",
            "subtitle": "Selecciona cómo quieres pagar esta lectura de Tarot.",
            "usd": f"Pagar en dólares — {usd}",
            "brl": f"Pagar en reales brasileños — {brl}",
            "note": "Serás redirigido al checkout seguro de Stripe.",
        },
    }[normalize_language(language)]

    safe_token = html.escape(token, quote=True)
    return f"""<!doctype html>
<html lang="{html.escape(language)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(labels['title'])}</title>
<style>
body {{ margin:0; background:#101014; color:#f6f3ff; font-family:Arial,sans-serif; }}
main {{ max-width:520px; margin:0 auto; padding:48px 22px; text-align:center; }}
.card {{ background:#1b1a22; border:1px solid #34303f; border-radius:18px; padding:28px; }}
h1 {{ font-size:25px; margin:0 0 12px; }}
p {{ line-height:1.5; color:#ccc6d8; }}
a.button {{ display:block; margin:14px 0; padding:16px 18px; border-radius:12px; text-decoration:none; font-weight:700; background:#f6f3ff; color:#17131d; }}
a.button.secondary {{ background:#d8c5ff; }}
small {{ color:#9e97aa; }}
</style>
</head>
<body><main><div class="card">
<h1>{html.escape(labels['title'])}</h1>
<p>{html.escape(labels['subtitle'])}</p>
<a class="button" href="/api/payments/choose/{safe_token}/start?currency=usd">{html.escape(labels['usd'])}</a>
<a class="button secondary" href="/api/payments/choose/{safe_token}/start?currency=brl">{html.escape(labels['brl'])}</a>
<small>{html.escape(labels['note'])}</small>
</div></main></body></html>"""


def _admin_bypass_html(language: str) -> str:
    labels = {
        "en": (
            "Administrator test access confirmed",
            "No payment was charged. Return to WhatsApp; the Tarot reading is continuing automatically.",
        ),
        "pt": (
            "Acesso de teste de administrador confirmado",
            "Nenhum pagamento foi cobrado. Volte ao WhatsApp; a leitura de Tarô está continuando automaticamente.",
        ),
        "es": (
            "Acceso de prueba de administrador confirmado",
            "No se realizó ningún cobro. Vuelve a WhatsApp; la lectura de Tarot continúa automáticamente.",
        ),
    }[normalize_language(language)]
    return (
        "<html><body style='font-family:sans-serif;text-align:center;padding:40px'>"
        f"<h2>{html.escape(labels[0])}</h2>"
        f"<p>{html.escape(labels[1])}</p>"
        "</body></html>"
    )


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


@router.get("/choose/{choice_token}", response_class=HTMLResponse)
def choose_payment_currency(
    choice_token: str,
    db: Session = Depends(get_db),
) -> str:
    payment = tarot_payment_service.get_by_choice_token(db, choice_token)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found.")
    if payment.status != "PENDING":
        return (
            "<html><body style='font-family:sans-serif;text-align:center;padding:40px'>"
            "<h2>This payment is no longer pending.</h2>"
            "<p>Return to WhatsApp to continue.</p>"
            "</body></html>"
        )

    language = _payment_language(db, payment.conversation_id)
    return _choice_html(token=choice_token, language=language)


@router.get("/choose/{choice_token}/start")
def start_checkout_in_currency(
    choice_token: str,
    currency: str = Query(..., pattern="^(usd|brl)$"),
    db: Session = Depends(get_db),
):
    payment = tarot_payment_service.get_by_choice_token(db, choice_token)
    if payment is None:
        raise HTTPException(status_code=404, detail="Payment not found.")

    language = _payment_language(db, payment.conversation_id)
    try:
        payment = tarot_payment_service.choose_currency(
            db=db,
            choice_token=choice_token,
            currency=currency,
            language=language,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PaymentConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PaymentProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    conversation = db.get(WhatsAppConversationEntity, payment.conversation_id)
    if conversation is not None and conversation.state == "RITUAL_AWAITING_PAYMENT":
        flow = whatsapp_tarot_flow_store.get(db, conversation.id)
        flow["payment_session_id"] = payment.provider_session_id
        flow["payment_url"] = payment.checkout_url
        flow["payment_currency"] = payment.currency
        whatsapp_tarot_flow_store.save(db, conversation.id, flow)
        db.commit()

    return RedirectResponse(url=payment.checkout_url, status_code=303)


@router.get("/admin-bypass/{choice_token}", response_class=HTMLResponse)
def admin_payment_bypass(
    choice_token: str,
    db: Session = Depends(get_db),
) -> str:
    try:
        payment, changed = tarot_payment_service.activate_admin_bypass(
            db=db,
            choice_token=choice_token,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    language = _payment_language(db, payment.conversation_id)
    if changed:
        to_number, messages = ritual_whatsapp_conversation_service.resume_after_payment(
            db=db,
            conversation_id=payment.conversation_id,
            provider_session_id=payment.provider_session_id,
        )
        if to_number and messages:
            from app.whatsapp.ritual_webhook import _dispatch_outgoing

            _dispatch_outgoing(db=db, to=to_number, messages=messages)

    return _admin_bypass_html(language)


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

    event_data = event.to_dict()
    event_type = str(event_data.get("type") or "")
    obj = (event_data.get("data") or {}).get("object") or {}

    # The same signed Stripe endpoint handles both per-reading payments and
    # the Daily Tarot + Weekly Astrology plan. Plan handlers return None for
    # unrelated events, preserving the existing Tarot payment flow.
    plan_status = handle_plan_stripe_event(db=db, event_type=event_type, obj=obj)
    if plan_status is not None:
        return {"status": plan_status}

    session_id = str(obj.get("id") or "")
    if not session_id:
        return {"status": "ignored"}

    if event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
        if event_type == "checkout.session.completed" and obj.get("payment_status") != "paid":
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
