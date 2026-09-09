import httpx

from app.whatsapp.config import get_whatsapp_settings


class WhatsAppConfigurationError(RuntimeError):
    pass


class WhatsAppProviderError(RuntimeError):
    pass


class WhatsAppCloudClient:
    def _settings(self):
        settings = get_whatsapp_settings()
        missing = []

        if not settings.access_token:
            missing.append("WHATSAPP_ACCESS_TOKEN")
        if not settings.phone_number_id:
            missing.append("WHATSAPP_PHONE_NUMBER_ID")
        if not settings.graph_version:
            missing.append("WHATSAPP_GRAPH_VERSION")

        if missing:
            raise WhatsAppConfigurationError(
                "Missing WhatsApp configuration: " + ", ".join(missing)
            )

        return settings

    def send_text(self, *, to: str, body: str) -> list[dict]:
        settings = self._settings()
        url = (
            f"https://graph.facebook.com/{settings.graph_version}/"
            f"{settings.phone_number_id}/messages"
        )

        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        }

        chunks = self._split_text(body, max_chars=3500)
        sent_messages = []

        with httpx.Client(timeout=30.0) as client:
            for chunk in chunks:
                response = client.post(
                    url,
                    headers=headers,
                    json={
                        "messaging_product": "whatsapp",
                        "recipient_type": "individual",
                        "to": to.lstrip("+"),
                        "type": "text",
                        "text": {
                            "preview_url": False,
                            "body": chunk,
                        },
                    },
                )

                if response.is_error:
                    raise WhatsAppProviderError(
                        "WhatsApp send failed "
                        f"({response.status_code}): {response.text}"
                    )

                payload = response.json()
                messages = payload.get("messages") or []
                if not messages or not messages[0].get("id"):
                    raise WhatsAppProviderError(
                        "WhatsApp send succeeded but provider returned no message id."
                    )

                provider_message = messages[0]
                sent_messages.append(
                    {
                        "id": provider_message["id"],
                        "status": provider_message.get("message_status"),
                        "body": chunk,
                    }
                )

        return sent_messages

    @staticmethod
    def _split_text(text: str, *, max_chars: int) -> list[str]:
        text = text.strip()
        if len(text) <= max_chars:
            return [text]

        chunks = []
        remaining = text

        while len(remaining) > max_chars:
            split_at = remaining.rfind("\n", 0, max_chars)
            if split_at < max_chars // 2:
                split_at = remaining.rfind(" ", 0, max_chars)
            if split_at < max_chars // 2:
                split_at = max_chars

            chunks.append(remaining[:split_at].strip())
            remaining = remaining[split_at:].strip()

        if remaining:
            chunks.append(remaining)

        return chunks


whatsapp_cloud_client = WhatsAppCloudClient()
