import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class WhatsAppSettings:
    verify_token: str | None
    access_token: str | None
    phone_number_id: str | None
    graph_version: str | None
    app_secret: str | None


def get_whatsapp_settings() -> WhatsAppSettings:
    return WhatsAppSettings(
        verify_token=os.getenv("WHATSAPP_VERIFY_TOKEN"),
        access_token=os.getenv("WHATSAPP_ACCESS_TOKEN"),
        phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID"),
        graph_version=os.getenv("WHATSAPP_GRAPH_VERSION"),
        app_secret=os.getenv("WHATSAPP_APP_SECRET"),
    )
