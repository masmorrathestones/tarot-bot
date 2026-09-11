from __future__ import annotations

import base64
import hashlib
import hmac
import mimetypes
import secrets
import time
from pathlib import Path
from urllib.parse import quote

import httpx

from app.social.x.config import get_x_settings


class XConfigurationError(RuntimeError):
    pass


class XProviderError(RuntimeError):
    pass


PROJECT_ROOT = Path(__file__).resolve().parents[3]
MEDIA_UPLOAD_URL = "https://upload.x.com/1.1/media/upload.json"


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


def _posting_auth(url: str) -> str:
    settings = get_x_settings()
    if not settings.posting_configured:
        raise XConfigurationError(
            "X posting credentials are incomplete. Configure X_API_KEY, "
            "X_API_SECRET, X_ACCESS_TOKEN and X_ACCESS_TOKEN_SECRET."
        )
    return _oauth_header(
        method="POST",
        url=url,
        api_key=str(settings.api_key),
        api_secret=str(settings.api_secret),
        access_token=str(settings.access_token),
        access_token_secret=str(settings.access_token_secret),
    )


def _resolve_media_path(media_path: str) -> Path:
    candidate = (PROJECT_ROOT / media_path).resolve()
    try:
        candidate.relative_to(PROJECT_ROOT)
    except ValueError as exc:
        raise XConfigurationError("media_path must stay inside the project directory.") from exc
    if not candidate.is_file():
        raise XConfigurationError(f"Media file does not exist: {media_path}")
    return candidate


class XClient:
    def search_recent(self, query: str, *, max_results: int = 10) -> list[dict[str, str | None]]:
        settings = get_x_settings()
        if not settings.bearer_token:
            raise XConfigurationError(
                "X_BEARER_TOKEN is not configured for recent-search requests."
            )

        url = f"{settings.api_base_url}/2/tweets/search/recent"
        try:
            response = httpx.get(
                url,
                headers={"Authorization": f"Bearer {settings.bearer_token}"},
                params={
                    "query": query,
                    "max_results": max(10, min(100, max_results)),
                    "tweet.fields": "author_id,created_at,lang",
                    "expansions": "author_id",
                    "user.fields": "username",
                },
                timeout=20.0,
            )
        except httpx.HTTPError as exc:
            raise XProviderError(f"X recent search failed: {exc}") from exc

        if response.status_code != 200:
            detail = response.text.strip()
            raise XProviderError(
                f"X recent search returned HTTP {response.status_code}: {detail[:1500]}"
            )

        try:
            payload = response.json()
            users = {
                str(user.get("id")): str(user.get("username") or "")
                for user in (payload.get("includes") or {}).get("users", [])
                if user.get("id")
            }
            rows: list[dict[str, str | None]] = []
            for tweet in payload.get("data") or []:
                tweet_id = str(tweet.get("id") or "").strip()
                text = str(tweet.get("text") or "").strip()
                if not tweet_id or not text:
                    continue
                author_id = str(tweet.get("author_id") or "").strip() or None
                rows.append(
                    {
                        "tweet_id": tweet_id,
                        "text": text,
                        "author_id": author_id,
                        "author_username": users.get(author_id or "") or None,
                        "language": str(tweet.get("lang") or "").strip() or None,
                        "created_at": str(tweet.get("created_at") or "").strip() or None,
                    }
                )
            return rows
        except (ValueError, AttributeError, TypeError) as exc:
            raise XProviderError("X recent search returned invalid JSON.") from exc

    def upload_image(self, media_path: str) -> str:
        path = _resolve_media_path(media_path)
        if path.stat().st_size > 5 * 1024 * 1024:
            raise XConfigurationError("X image uploads must be 5 MB or smaller.")

        authorization = _posting_auth(MEDIA_UPLOAD_URL)
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        try:
            with path.open("rb") as media_file:
                response = httpx.post(
                    MEDIA_UPLOAD_URL,
                    headers={"Authorization": authorization},
                    files={"media": (path.name, media_file, content_type)},
                    timeout=60.0,
                )
        except httpx.HTTPError as exc:
            raise XProviderError(f"X media upload failed: {exc}") from exc

        if response.status_code not in (200, 201, 202):
            detail = response.text.strip()
            raise XProviderError(
                f"X media upload returned HTTP {response.status_code}: {detail[:1500]}"
            )

        try:
            payload = response.json()
            media_id = str(
                payload.get("media_id_string")
                or payload.get("media_id")
                or (payload.get("data") or {}).get("id")
                or ""
            ).strip()
        except (ValueError, AttributeError) as exc:
            raise XProviderError("X media upload returned invalid JSON.") from exc
        if not media_id:
            raise XProviderError("X media upload response did not include a media id.")
        return media_id

    def create_post(
        self,
        text: str,
        *,
        media_path: str | None = None,
        reply_to_post_id: str | None = None,
    ) -> str:
        settings = get_x_settings()
        url = f"{settings.api_base_url}/2/tweets"
        authorization = _posting_auth(url)

        body: dict[str, object] = {"text": text}
        if media_path:
            media_id = self.upload_image(media_path)
            body["media"] = {"media_ids": [media_id]}
        if reply_to_post_id:
            body["reply"] = {"in_reply_to_tweet_id": str(reply_to_post_id)}

        try:
            response = httpx.post(
                url,
                headers={
                    "Authorization": authorization,
                    "Content-Type": "application/json",
                },
                json=body,
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
