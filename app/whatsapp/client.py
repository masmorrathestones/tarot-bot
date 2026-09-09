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
        chunks = self._split_text(body, max_chars=3500)
        sent_messages = []

        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            for chunk in chunks:
                provider_message = self._post_message(
                    client=client,
                    to=to,
                    message_payload={
                        "type": "text",
                        "text": {
                            "preview_url": False,
                            "body": chunk,
                        },
                    },
                )
                sent_messages.append(
                    {
                        "id": provider_message["id"],
                        "status": provider_message.get("message_status"),
                        "body": chunk,
                    }
                )

        return sent_messages

    def send_image(
        self,
        *,
        to: str,
        image_url: str,
        caption: str,
    ) -> list[dict]:
        with httpx.Client(timeout=30.0, follow_redirects=True) as client:
            provider_message = self._post_message(
                client=client,
                to=to,
                message_payload={
                    "type": "image",
                    "image": {
                        "link": image_url,
                        "caption": caption[:1024],
                    },
                },
            )

        return [
            {
                "id": provider_message["id"],
                "status": provider_message.get("message_status"),
                "body": caption[:1024],
            }
        ]

    def _post_message(
        self,
        *,
        client: httpx.Client,
        to: str,
        message_payload: dict,
    ) -> dict:
        settings = self._settings()
        url = (
            f"https://graph.facebook.com/{settings.graph_version}/"
            f"{settings.phone_number_id}/messages"
        )
        headers = {
            "Authorization": f"Bearer {settings.access_token}",
            "Content-Type": "application/json",
        }
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to.lstrip("+"),
            **message_payload,
        }

        response = client.post(url, headers=headers, json=payload)
        if response.is_error:
            raise WhatsAppProviderError(
                "WhatsApp send failed "
                f"({response.status_code}): {response.text}"
            )

        response_payload = response.json()
        messages = response_payload.get("messages") or []
        if not messages or not messages[0].get("id"):
            raise WhatsAppProviderError(
                "WhatsApp send succeeded but provider returned no message id."
            )
        return messages[0]

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
