from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import time
from urllib.parse import quote

import httpx

from app.social.x.config import get_x_settings


class XConfigurationError(RuntimeError):
    pass


class XProviderError(RuntimeError):
    pass


def _pct(value: str) -> str:
    return quote(value, safe="~-._")


def _oauth_header(*, method: str, url: str, api_key: str, api_secret: str, access_token: str, access_token_secret: str) -> str:
    oauth = {
        "oauth_consumer_key": api_key,
        "oauth_nonce": secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_token": access_token,
        "oauth_version": "1.0",
    }
    normalized = "&".join(
        f"{_pct(str(key))}={_pct(str(value))}"
        for key, value in sorted(oauth.items())
    )
    base_string = "&".join((_pct(method.upper()), _pct(url), _pct(normalized)))
    signing_key = f"{_pct(api_secret)}&{_pct(access_token_secret)}"
    signature = base64.b64encode(
        hmac.new(
            signing_key.encode("utf-8"),
            base_string.encode("utf-8"),
            hashlib.sha1,
        ).digest()
    ).decode("ascii")
    oauth["oauth_signature"] = signature
    return "OAuth " + ", ".join(
        f'{_pct(key)}="{_pct(value)}"' for key, value in sorted(oauth.items())
    )


class XClient:
    def create_post(self, text: str) -> str:
        settings = get_x_settings()
        if not settings.posting_configured:
            raise XConfigurationError(
                "X posting credentials are incomplete. Configure X_API_KEY, "
                "X_API_SECRET, X_ACCESS_TOKEN and X_ACCESS_TOKEN_SECRET."
            )

        url = f"{settings.api_base_url}/2/tweets"
        authorization = _oauth_header(
            method="POST",
            url=url,
            api_key=str(settings.api_key),
            api_secret=str(settings.api_secret),
            access_token=str(settings.access_token),
            access_token_secret=str(settings.access_token_secret),
        )
        try:
            response = httpx.post(
                url,
                headers={
                    "Authorization": authorization,
                    "Content-Type": "application/json",
                },
                json={"text": text},
                timeout=20.0,
            )
        except httpx.HTTPError as exc:
            raise XProviderError(f"X API request failed: {exc}") from exc

        if response.status_code != 201:
            detail = response.text.strip()
            raise XProviderError(
                f"X API returned HTTP {response.status_code}: {detail[:1500]}"
            )

        try:
            payload = response.json()
            post_id = str((payload.get("data") or {}).get("id") or "").strip()
        except (ValueError, AttributeError) as exc:
            raise XProviderError("X API returned an invalid JSON response.") from exc
        if not post_id:
            raise XProviderError("X API response did not include the created post id.")
        return post_id


x_client = XClient()
