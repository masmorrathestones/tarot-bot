from fastapi import FastAPI
from app.tarot.router import router as tarot_router
from app.users.router import router as user_router
from app.whatsapp.webhook import router as whatsapp_router

app = FastAPI(
    title="Tarot Bot API",
    version="0.5.0",
    description="API inicial para sorteio estruturado de cartas de Tarot."
)

app.include_router(user_router)
app.include_router(tarot_router)
app.include_router(whatsapp_router)


@app.get("/")
def root():
    return {
        "status": "online",
        "service": "tarot-bot",
        "version": "0.5.0"
    }


@app.get("/health")
def health():
    return {"status": "ok"}
