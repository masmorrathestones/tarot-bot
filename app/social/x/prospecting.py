from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai.provider import OpenAITextProvider
from app.database.session import SessionLocal
from app.social.x.client import x_client
from app.social.x.config import get_x_settings
from app.social.x.models import XReplyOpportunityEntity


class XReplyOpportunityNotFoundError(RuntimeError):
    pass


class XReplyOpportunityStateError(RuntimeError):
    pass


DIRECT_INTENT_TERMS = (
    "tarot reading",
    "tarot reader",
    "leitura de tarot",
    "leitura de tarô",
    "tiragem",
    "lectura de tarot",
    "lector de tarot",
    "lectora de tarot",
)

INTENT_TERMS = (
    "need",
    "looking for",
    "recommend",
    "anyone",
    "preciso",
    "alguém",
    "indica",
    "recomenda",
    "busco",
    "recomienda",
    "alguien",
)

CONTEXT_TERMS = (
    "tarot",
    "tarô",
    "astrology",
    "astrologia",
    "horoscope",
    "horóscopo",
    "mapa astral",
)


def score_opportunity(text: str) -> int:
    lowered = text.casefold()
    score = 0
    if any(term in lowered for term in DIRECT_INTENT_TERMS):
        score += 5
    if any(term in lowered for term in INTENT_TERMS):
        score += 3
    if any(term in lowered for term in CONTEXT_TERMS):
        score += 1
    if "?" in text:
        score += 1
    return score


def _reply_instructions() -> str:
    return (
        "You write replies for the public X/Twitter profile Holomancy Tarot. "
        "Create a natural, clever and attention-catching reply to the supplied public post. "
        "Match the post's language. Keep it conversational and specific to what the person wrote. "
        "If it fits naturally, mention that Holomancy offers a complete Tarot reading combining "
        "Tarot, astrology and personality for US$1, but keep the offer subtle rather than salesy. "
        "Do not pretend to know the person, do not invent facts about their life, do not make "
        "deterministic supernatural claims, do not pressure them, and do not imply urgency or fear. "
        "Avoid generic engagement bait, hashtags and canned marketing language. "
        "Return only the reply text, at most 240 characters."
    )


def generate_reply(*, tweet_text: str, language: str | None, author_username: str | None) -> str:
    provider = OpenAITextProvider()
    input_text = (
        f"Language hint: {language or 'unknown'}\n"
        f"Author: @{author_username or 'unknown'}\n"
        f"Public post:\n{tweet_text}\n"
    )
    reply = provider.generate(
        instructions=_reply_instructions(),
        input_text=input_text,
    ).strip()
    if len(reply) > 280:
        reply = reply[:277].rstrip() + "..."
    return reply


def discover_x_opportunities() -> int:
    settings = get_x_settings()
    if not settings.prospecting_enabled or not settings.search_configured:
        return 0

    db = SessionLocal()
    created = 0
    try:
        for query in settings.prospect_queries:
            if created >= settings.prospecting_max_per_run:
                break
            results = x_client.search_recent(query, max_results=10)
            for result in results:
                if created >= settings.prospecting_max_per_run:
                    break

                tweet_id = str(result.get("tweet_id") or "").strip()
                tweet_text = str(result.get("text") or "").strip()
                if not tweet_id or not tweet_text:
                    continue

                exists = db.scalar(
                    select(XReplyOpportunityEntity.id).where(
                        XReplyOpportunityEntity.tweet_id == tweet_id
                    )
                )
                if exists is not None:
                    continue

                score = score_opportunity(tweet_text)
                if score < settings.prospecting_min_score:
                    continue

                row = XReplyOpportunityEntity(
                    tweet_id=tweet_id,
                    tweet_text=tweet_text,
                    author_id=result.get("author_id"),
                    author_username=result.get("author_username"),
                    language=result.get("language"),
                    matched_query=query,
                    score=score,
                    status="DISCOVERED",
                )
                db.add(row)
                db.commit()
                db.refresh(row)

                try:
                    row.suggested_reply = generate_reply(
                        tweet_text=row.tweet_text,
                        language=row.language,
                        author_username=row.author_username,
                    )
                    row.status = "GENERATED"
                    row.error_message = None
                except Exception as exc:
                    row.status = "FAILED"
                    row.error_message = str(exc)[:2000]
                db.commit()
                created += 1
        return created
    finally:
        db.close()


def list_opportunities(
    *,
    db: Session,
    status: str | None = None,
    limit: int = 50,
) -> list[XReplyOpportunityEntity]:
    statement = select(XReplyOpportunityEntity)
    if status:
        statement = statement.where(XReplyOpportunityEntity.status == status.upper())
    statement = statement.order_by(
        XReplyOpportunityEntity.score.desc(),
        XReplyOpportunityEntity.created_at.desc(),
    ).limit(limit)
    return list(db.scalars(statement).all())


def approve_opportunity(
    *,
    db: Session,
    opportunity_id: int,
    reply_text: str | None = None,
) -> XReplyOpportunityEntity:
    row = db.get(XReplyOpportunityEntity, opportunity_id)
    if row is None:
        raise XReplyOpportunityNotFoundError("X reply opportunity not found.")
    if row.status != "GENERATED":
        raise XReplyOpportunityStateError(
            f"Only GENERATED opportunities can be approved; current status is {row.status}."
        )

    final_reply = (reply_text or row.suggested_reply or "").strip()
    if not final_reply:
        raise XReplyOpportunityStateError("Opportunity has no reply text to publish.")
    if len(final_reply) > 280:
        raise XReplyOpportunityStateError("Reply must be 280 characters or fewer.")

    try:
        row.status = "POSTING"
        db.commit()
        reply_id = x_client.create_post(final_reply, reply_to_post_id=row.tweet_id)
        row.suggested_reply = final_reply
        row.x_reply_id = reply_id
        row.status = "POSTED"
        row.replied_at = datetime.now(timezone.utc)
        row.error_message = None
        db.commit()
        db.refresh(row)
        return row
    except Exception as exc:
        row.status = "FAILED"
        row.error_message = str(exc)[:2000]
        db.commit()
        raise


def reject_opportunity(*, db: Session, opportunity_id: int) -> XReplyOpportunityEntity:
    row = db.get(XReplyOpportunityEntity, opportunity_id)
    if row is None:
        raise XReplyOpportunityNotFoundError("X reply opportunity not found.")
    if row.status not in {"DISCOVERED", "GENERATED", "FAILED"}:
        raise XReplyOpportunityStateError(
            f"Opportunity in status {row.status} cannot be rejected."
        )
    row.status = "REJECTED"
    row.error_message = None
    db.commit()
    db.refresh(row)
    return row
