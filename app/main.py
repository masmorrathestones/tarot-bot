import asyncio

from fastapi import FastAPI

from app.assets.router import router as assets_router
from app.assets.ritual_router import router as ritual_assets_router
from app.payments.router import router as payments_router
from app.plans.router import router as plans_router
from app.plans.scheduler import plan_scheduler_loop
from app.tarot.router import router as tarot_router
from app.users.router import router as user_router
from app.whatsapp.ritual_webhook import router as whatsapp_router

app = FastAPI(
    title="Tarot Bot API",
    version="0.12.0",
    description="API for structured Tarot card draws, symbolic profiles, payments, subscriptions, and AI-assisted readings."
)

app.include_router(user_router)
app.include_router(tarot_router)
app.include_router(whatsapp_router)
app.include_router(payments_router)
app.include_router(plans_router)
app.include_router(assets_router)
app.include_router(ritual_assets_router)


@app.on_event("startup")
async def start_plan_scheduler() -> None:
    app.state.plan_scheduler_task = asyncio.create_task(plan_scheduler_loop())


@app.on_event("shutdown")
async def stop_plan_scheduler() -> None:
    task = getattr(app.state, "plan_scheduler_task", None)
    if task is not None:
        task.cancel()


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "tarot-bot",
        "version": "0.12.0"
    }


@app.get("/health")
def health():
    return {"status": "ok"}
