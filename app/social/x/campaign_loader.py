from __future__ import annotations

import json
from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from sqlalchemy import select

from app.database.session import SessionLocal
from app.social.x.models import ScheduledXPostEntity


CAMPAIGN_FILE = Path(__file__).resolve().parent / "campaigns" / "latest.json"


def import_latest_campaign() -> int:
    """Import the Git-managed campaign once, idempotently."""
    if not CAMPAIGN_FILE.exists():
        return 0

    payload = json.loads(CAMPAIGN_FILE.read_text(encoding="utf-8"))
    campaign_id = str(payload.get("campaign_id") or "").strip()
    if not campaign_id:
        raise ValueError("X campaign requires a non-empty campaign_id.")

    timezone_name = str(payload.get("timezone") or "America/Sao_Paulo").strip()
    tz = ZoneInfo(timezone_name)
    now_local = datetime.now(timezone.utc).astimezone(tz)

    explicit_start = payload.get("start_date")
    if explicit_start:
        base_date = datetime.strptime(str(explicit_start), "%Y-%m-%d").date()
    else:
        base_date = now_local.date() + timedelta(days=1)

    posts = payload.get("posts")
    if not isinstance(posts, list):
        raise ValueError("X campaign posts must be a list.")

    post_keys: set[str] = set()
    for index, item in enumerate(posts, start=1):
        if not isinstance(item, dict):
            raise ValueError(f"Invalid campaign post at index {index}.")
        post_key = str(item.get("key") or index).strip()
        if post_key in post_keys:
            raise ValueError(f"Duplicate campaign post key: {post_key}")
        post_keys.add(post_key)

    db = SessionLocal()
    inserted = 0
    try:
        for index, item in enumerate(posts, start=1):
            post_key = str(item.get("key") or index).strip()
            source_key = f"{campaign_id}:{post_key}"[:160]
            if db.scalar(
                select(ScheduledXPostEntity.id).where(
                    ScheduledXPostEntity.source_key == source_key
                )
            ) is not None:
                continue

            text_value = str(item.get("text") or "").strip()
            if not text_value:
                raise ValueError(f"Campaign post {post_key} has empty text.")

            day_offset = int(item.get("day_offset") or 0)
            if day_offset < 0:
                raise ValueError(f"Campaign post {post_key} has negative day_offset.")

            hour_text = str(item.get("time") or "").strip()
            scheduled_time = time.fromisoformat(hour_text)
            local_dt = datetime.combine(
                base_date + timedelta(days=day_offset),
                scheduled_time,
                tzinfo=tz,
            )

            reply_to = str(item.get("reply_to") or "").strip()
            parent_source_key = None
            if reply_to:
                if reply_to not in post_keys:
                    raise ValueError(
                        f"Campaign post {post_key} references unknown parent {reply_to}."
                    )
                parent_source_key = f"{campaign_id}:{reply_to}"[:160]

            media_path = str(item.get("media_path") or "").strip() or None

            db.add(
                ScheduledXPostEntity(
                    text=text_value,
                    language=(str(item.get("language") or "").strip().lower() or None),
                    source_key=source_key,
                    media_path=media_path,
                    parent_source_key=parent_source_key,
                    scheduled_at=local_dt.astimezone(timezone.utc),
                    status="PENDING",
                )
            )
            inserted += 1

        db.commit()
        return inserted
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
