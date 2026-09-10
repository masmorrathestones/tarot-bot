from __future__ import annotations

import html
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.plans.config import get_plan_settings
from app.plans.models import DailyWeeklyPlanEntity
from app.plans.service import PlanConfigurationError, PlanProviderError, daily_weekly_plan_service
from app.users.service import user_service
from app.whatsapp.i18n import normalize_language
from app.whatsapp.repository import whatsapp_repository
from app.whatsapp.webhook import _send_outgoing


router = APIRouter(prefix="/api/plans", tags=["Plans"])


def _money(currency: str, cents: int) -> str:
    if currency == "brl":
        return f"R$ {cents / 100:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"US$ {cents / 100:.2f}"


def _language_for_user(db: Session, user_id: int) -> str:
    user = user_service.get(db, user_id)
    conversation, _ = whatsapp_repository.get_or_create_conversation_by_number(
        db, whatsapp_number=user.whatsapp_number, user_id=user.id
    )
    return normalize_language(conversation.language)


def _is_admin(db: Session, user_id: int) -> bool:
    value = db.execute(
        text("SELECT is_admin FROM users WHERE id = :user_id"),
        {"user_id": user_id},
    ).scalar_one_or_none()
    return bool(value)


def _checkout_html(plan: DailyWeeklyPlanEntity, language: str) -> str:
    settings = get_plan_settings()
    billing = plan.billing_type or "recurring"
    usd = _money("usd", settings.amount(billing_type=billing, currency="usd"))
    brl = _money("brl", settings.amount(billing_type=billing, currency="brl"))
    labels = {
        "en": ("Choose payment currency", f"US dollars — {usd}", f"Brazilian reais — {brl}", "You will be redirected to Stripe's secure checkout."),
        "pt": ("Escolha a moeda do pagamento", f"Dólar — {usd}", f"Real — {brl}", "Você será redirecionado ao checkout seguro da Stripe."),
        "es": ("Elige la moneda del pago", f"Dólares — {usd}", f"Reales brasileños — {brl}", "Serás redirigido al checkout seguro de Stripe."),
    }[language]
    token = html.escape(plan.checkout_token or "", quote=True)
    return f"""<!doctype html><html lang="{language}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(labels[0])}</title><style>body{{margin:0;background:#101014;color:#f6f3ff;font-family:Arial,sans-serif}}main{{max-width:520px;margin:0 auto;padding:48px 22px;text-align:center}}.card{{background:#1b1a22;border:1px solid #34303f;border-radius:18px;padding:28px}}a{{display:block;margin:14px 0;padding:16px;border-radius:12px;text-decoration:none;font-weight:700;background:#f6f3ff;color:#17131d}}a.alt{{background:#d8c5ff}}p{{color:#ccc6d8;line-height:1.5}}</style></head><body><main><div class="card"><h1>{html.escape(labels[0])}</h1><a href="/api/plans/checkout/{token}/start?currency=usd">{html.escape(labels[1])}</a><a class="alt" href="/api/plans/checkout/{token}/start?currency=brl">{html.escape(labels[2])}</a><p>{html.escape(labels[3])}</p></div></main></body></html>"""


def _admin_checkout_html(plan: DailyWeeklyPlanEntity, language: str) -> str:
    labels = {
        "en": (
            "Administrator access",
            "Your administrator account can activate this plan without a real charge. This creates 30 days of test access and does not create a Stripe subscription.",
            "Activate plan without payment",
        ),
        "pt": (
            "Acesso de administrador",
            "Sua conta de administrador pode ativar este plano sem cobrança real. Isso cria 30 dias de acesso para testes e não cria uma assinatura na Stripe.",
            "Ativar plano sem pagamento",
        ),
        "es": (
            "Acceso de administrador",
            "Tu cuenta de administrador puede activar este plan sin un cobro real. Esto crea 30 días de acceso de prueba y no crea una suscripción en Stripe.",
            "Activar plan sin pago",
        ),
    }[language]
    token = html.escape(plan.checkout_token or "", quote=True)
    return f"""<!doctype html><html lang="{language}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{html.escape(labels[0])}</title><style>body{{margin:0;background:#101014;color:#f6f3ff;font-family:Arial,sans-serif}}main{{max-width:520px;margin:0 auto;padding:48px 22px;text-align:center}}.card{{background:#1b1a22;border:1px solid #34303f;border-radius:18px;padding:28px}}a{{display:block;margin:18px 0;padding:16px;border-radius:12px;text-decoration:none;font-weight:700;background:#d8c5ff;color:#17131d}}p{{color:#ccc6d8;line-height:1.5}}</style></head><body><main><div class="card"><h1>{html.escape(labels[0])}</h1><p>{html.escape(labels[1])}</p><a href="/api/plans/admin-bypass/{token}">{html.escape(labels[2])}</a></div></main></body></html>"""


def _admin_success_html(language: str) -> str:
    title, body = {
        "en": ("Plan activated", "Administrator test access was activated without any charge. You can return to WhatsApp."),
        "pt": ("Plano ativado", "O acesso de teste do administrador foi ativado sem nenhuma cobrança. Você já pode voltar ao WhatsApp."),
        "es": ("Plan activado", "El acceso de prueba del administrador fue activado sin ningún cobro. Ya puedes volver a WhatsApp."),
    }[language]
    return f"<html><body style='font-family:sans-serif;text-align:center;padding:40px'><h2>{html.escape(title)}</h2><p>{html.escape(body)}</p></body></html>"


@router.get("/checkout/{token}", response_class=HTMLResponse)
def plan_checkout_choice(token: str, db: Session = Depends(get_db)) -> str:
    plan = daily_weekly_plan_service.get_by_checkout_token(db, token)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan checkout not found.")
    if plan.status != "AWAITING_PAYMENT":
        raise HTTPException(status_code=409, detail="Plan checkout is no longer pending.")
    language = _language_for_user(db, plan.user_id)
    if _is_admin(db, plan.user_id):
        return _admin_checkout_html(plan, language)
    return _checkout_html(plan, language)


@router.get("/admin-bypass/{token}", response_class=HTMLResponse)
def plan_admin_bypass(token: str, db: Session = Depends(get_db)) -> str:
    plan = daily_weekly_plan_service.get_by_checkout_token(db, token)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan checkout not found.")
    if not _is_admin(db, plan.user_id):
        raise HTTPException(status_code=403, detail="Administrator access is not enabled for this user.")

    language = _language_for_user(db, plan.user_id)
    if plan.status in {"ACTIVE", "CANCEL_AT_PERIOD_END"}:
        return _admin_success_html(language)
    if plan.status != "AWAITING_PAYMENT":
        raise HTTPException(status_code=409, detail="Plan checkout is no longer pending.")

    location = daily_weekly_plan_service.profile_location(db, plan.user_id)
    if location is None:
        raise HTTPException(status_code=409, detail="Current location is required before activation.")

    now = datetime.now(timezone.utc)
    plan.status = "CANCEL_AT_PERIOD_END"
    plan.billing_type = "one_time"
    plan.currency = "usd"
    plan.amount_cents = 0
    plan.stripe_checkout_session_id = None
    plan.stripe_customer_id = None
    plan.stripe_subscription_id = None
    plan.starts_at = now
    plan.current_period_end = now + timedelta(days=30)
    plan.cancel_at_period_end = True
    plan.schedule_timezone = str(location["current_timezone"])
    plan.next_daily_at = daily_weekly_plan_service.next_daily_occurrence(
        daily_time=plan.daily_time,
        timezone_name=plan.schedule_timezone,
        last_sent_at=plan.last_daily_sent_at,
        now=now,
    )
    plan.next_weekly_at = daily_weekly_plan_service.next_weekly_occurrence(
        weekday=plan.weekly_weekday,
        weekly_time=plan.weekly_time,
        timezone_name=plan.schedule_timezone,
        last_sent_at=plan.last_weekly_sent_at,
        now=now,
    )
    db.commit()
    db.refresh(plan)

    _send_activation_message(db, plan)
    return _admin_success_html(language)


@router.get("/checkout/{token}/start")
def plan_checkout_start(
    token: str,
    currency: str = Query(..., pattern="^(usd|brl)$"),
    db: Session = Depends(get_db),
):
    plan = daily_weekly_plan_service.get_by_checkout_token(db, token)
    if plan is None:
        raise HTTPException(status_code=404, detail="Plan checkout not found.")
    if _is_admin(db, plan.user_id):
        return RedirectResponse(url=f"/api/plans/admin-bypass/{token}", status_code=303)
    try:
        url = daily_weekly_plan_service.start_checkout(
            db=db,
            plan=plan,
            currency=currency,
            language=_language_for_user(db, plan.user_id),
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except PlanConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except PlanProviderError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return RedirectResponse(url=url, status_code=303)


@router.get("/success", response_class=HTMLResponse)
def plan_success() -> str:
    return "<html><body style='font-family:sans-serif;text-align:center;padding:40px'><h2>Plan payment confirmed</h2><p>You can return to WhatsApp. Your daily Tarot and weekly astrology schedule will activate automatically.</p></body></html>"


@router.get("/cancelled", response_class=HTMLResponse)
def plan_cancelled() -> str:
    return "<html><body style='font-family:sans-serif;text-align:center;padding:40px'><h2>Payment not completed</h2><p>Your plan has not been activated. Return to WhatsApp and send PLAN whenever you want to continue.</p></body></html>"


def handle_plan_stripe_event(*, db: Session, event_type: str, obj: dict) -> str | None:
    """Handle plan-specific events received by the existing signed Stripe webhook.

    Returns None when the event is unrelated to the plan so the normal Tarot
    payment webhook can continue handling it.
    """
    if event_type in {"checkout.session.completed", "checkout.session.async_payment_succeeded"}:
        metadata = obj.get("metadata") or {}
        if metadata.get("purpose") != "daily_weekly_plan":
            return None
        if event_type == "checkout.session.completed" and obj.get("mode") == "payment" and obj.get("payment_status") != "paid":
            return "awaiting_payment"
        plan = daily_weekly_plan_service.activate_from_checkout(db=db, session=obj)
        if plan is None:
            return "ignored"
        _send_activation_message(db, plan)
        return "plan_activated"

    if event_type == "invoice.paid":
        subscription_id = str(obj.get("subscription") or "")
        if not subscription_id:
            return None
        period_end = None
        lines = ((obj.get("lines") or {}).get("data") or [])
        if lines:
            raw_end = ((lines[0].get("period") or {}).get("end"))
            if raw_end:
                period_end = datetime.fromtimestamp(int(raw_end), tz=timezone.utc)
        plan = daily_weekly_plan_service.renew_subscription(
            db=db, subscription_id=subscription_id, period_end=period_end
        )
        return "plan_renewed" if plan else None

    if event_type == "customer.subscription.deleted":
        subscription_id = str(obj.get("id") or "")
        if not subscription_id:
            return None
        plan = daily_weekly_plan_service.mark_subscription_ended(db=db, subscription_id=subscription_id)
        return "plan_expired" if plan else None

    if event_type == "customer.subscription.updated":
        metadata = obj.get("metadata") or {}
        if metadata.get("purpose") != "daily_weekly_plan":
            return None
        subscription_id = str(obj.get("id") or "")
        plan = daily_weekly_plan_service.get_for_user(db, int(metadata.get("user_id") or 0)) if metadata.get("user_id") else None
        if plan and subscription_id == plan.stripe_subscription_id:
            plan.cancel_at_period_end = bool(obj.get("cancel_at_period_end"))
            if plan.cancel_at_period_end:
                plan.status = "CANCEL_AT_PERIOD_END"
            raw_end = obj.get("current_period_end")
            if raw_end:
                plan.current_period_end = datetime.fromtimestamp(int(raw_end), tz=timezone.utc)
            db.commit()
            return "plan_updated"
        return "ignored"

    return None


def _send_activation_message(db: Session, plan: DailyWeeklyPlanEntity) -> None:
    user = user_service.get(db, plan.user_id)
    language = _language_for_user(db, plan.user_id)
    daily = plan.daily_time.strftime("%H:%M") if plan.daily_time else "?"
    weekly = plan.weekly_time.strftime("%H:%M") if plan.weekly_time else "?"
    weekday = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")[plan.weekly_weekday or 0]
    message = {
        "pt": f"✅ *Plano ativado!*\n\nSua carta diária será enviada às {daily}. Sua análise astrológica semanal será enviada {weekday} às {weekly}.\n\nEnvie PLANO a qualquer momento para alterar os horários, atualizar seu local atual ou cancelar a renovação.",
        "es": f"✅ *¡Plan activado!*\n\nTu carta diaria se enviará a las {daily}. Tu análisis astrológico semanal se enviará {weekday} a las {weekly}.\n\nEnvía PLAN cuando quieras cambiar horarios, actualizar tu ubicación o cancelar la renovación.",
    }.get(language, f"✅ *Plan activated!*\n\nYour daily card will be sent at {daily}. Your weekly astrology analysis will be sent on {weekday} at {weekly}.\n\nSend PLAN anytime to change schedules, update your current location, or cancel renewal.")
    for sent in _send_outgoing(to=user.whatsapp_number, message=message):
        whatsapp_repository.register_outbound_message(
            db,
            whatsapp_message_id=sent["id"],
            to_number=user.whatsapp_number,
            text_body=sent["body"],
            provider_status=sent.get("status"),
        )