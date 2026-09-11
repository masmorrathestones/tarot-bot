import asyncio

from fastapi import FastAPI

from app.assets.router import router as assets_router
from app.assets.ritual_router import router as ritual_assets_router
from app.landing.router import router as landing_router
from app.payments.router import router as payments_router
from app.plans.router import router as plans_router
from app.plans.scheduler import plan_scheduler_loop
from app.social.x.manual_page import router as x_manual_reply_router
from app.social.x.router import router as x_scheduler_router
from app.social.x.scheduler import x_scheduler_loop
from app.tarot.router import router as tarot_router
from app.users.router import router as user_router
from app.whatsapp.ritual_webhook import router as whatsapp_router

app = FastAPI(
    title="Tarot Bot API",
    version="0.13.0",
    description="API for structured Tarot card draws, symbolic profiles, payments, subscriptions, AI-assisted readings, and scheduled X posts."
)

app.include_router(user_router)
app.include_router(tarot_router)
app.include_router(whatsapp_router)
app.include_router(payments_router)
app.include_router(plans_router)
app.include_router(x_scheduler_router)
app.include_router(x_manual_reply_router)
app.include_router(assets_router)
app.include_router(ritual_assets_router)
app.include_router(landing_router)


@app.on_event("startup")
async def start_background_schedulers() -> None:
    app.state.plan_scheduler_task = asyncio.create_task(plan_scheduler_loop())
    app.state.x_scheduler_task = asyncio.create_task(x_scheduler_loop())


@app.on_event("shutdown")
async def stop_background_schedulers() -> None:
    for attribute in ("plan_scheduler_task", "x_scheduler_task"):
        task = getattr(app.state, attribute, None)
        if task is not None:
            task.cancel()


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "tarot-bot",
        "version": "0.13.0"
    }


@app.get("/health")
def health():
    return {"status": "ok"}
