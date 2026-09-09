from fastapi import FastAPI
from app.assets.router import router as assets_router
from app.tarot.router import router as tarot_router
from app.users.router import router as user_router
from app.whatsapp.webhook import router as whatsapp_router

app = FastAPI(
    title="Tarot Bot API",
    version="0.7.0",
    description="API for structured Tarot card draws, symbolic profiles, and AI-assisted readings."
)

app.include_router(user_router)
app.include_router(tarot_router)
app.include_router(whatsapp_router)
app.include_router(assets_router)


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "tarot-bot",
        "version": "0.7.0"
    }


@app.get("/health")
def health():
    return {"status": "ok"}
