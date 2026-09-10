from __future__ import annotations

from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.persistence.models import DrawnCardEntity, ReadingEntity
from app.tarot.models import DrawnCard


PROFILE_ARCANA_CODE = {
    1: "THE_MAGICIAN", 2: "THE_HIGH_PRIESTESS", 3: "THE_EMPRESS", 4: "THE_EMPEROR",
    5: "THE_HIEROPHANT", 6: "THE_LOVERS", 7: "THE_CHARIOT", 8: "JUSTICE",
    9: "THE_HERMIT", 10: "WHEEL_OF_FORTUNE", 11: "STRENGTH", 12: "THE_HANGED_MAN",
    13: "DEATH", 14: "TEMPERANCE", 15: "THE_DEVIL", 16: "THE_TOWER",
    17: "THE_STAR", 18: "THE_MOON", 19: "THE_SUN", 20: "JUDGEMENT",
    21: "THE_WORLD", 22: "THE_FOOL",
}


def detect_symbolic_signals(
    db: Session,
    *,
    user_id: int,
    drawn_cards: list[DrawnCard],
    personal_arcana_number: int | None,
    year_arcana_number: int | None,
) -> list[dict]:
    """Compute recurrence/profile matches without delegating detection to AI."""
    current = {item.card.code: item.card.name for item in drawn_cards}
    if not current:
        return []

    recent_reading_ids = list(db.scalars(
        select(ReadingEntity.id)
        .where(ReadingEntity.user_id == user_id)
        .order_by(ReadingEntity.created_at.desc(), ReadingEntity.id.desc())
        .limit(4)
    ))
    recent_codes: set[str] = set()
    if recent_reading_ids:
        recent_codes = set(db.scalars(
            select(DrawnCardEntity.card_code)
            .where(DrawnCardEntity.reading_id.in_(recent_reading_ids))
        ))

    week_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    weekly_rows = db.execute(
        select(DrawnCardEntity.card_code)
        .join(ReadingEntity, ReadingEntity.id == DrawnCardEntity.reading_id)
        .where(
            ReadingEntity.user_id == user_id,
            ReadingEntity.created_at >= week_cutoff,
            DrawnCardEntity.card_code.in_(list(current.keys())),
        )
    ).all()
    weekly_counts = Counter(row[0] for row in weekly_rows)

    personal_code = PROFILE_ARCANA_CODE.get(personal_arcana_number or -1)
    year_code = PROFILE_ARCANA_CODE.get(year_arcana_number or -1)
    signals: list[dict] = []

    for code, name in current.items():
        if code in recent_codes:
            signals.append({
                "type": "last_four_recurrence",
                "card_code": code,
                "card_name": name,
                "message": f"{name} also appeared in at least one of the user's previous 4 Tarot readings.",
            })
        count = weekly_counts.get(code, 0)
        if count:
            signals.append({
                "type": "weekly_recurrence",
                "card_code": code,
                "card_name": name,
                "count": count,
                "message": f"{name} appeared {count} time(s) in the user's Tarot readings during the previous 7 days.",
            })
        if code == personal_code:
            signals.append({
                "type": "personal_arcana_match",
                "card_code": code,
                "card_name": name,
                "message": f"{name}, the user's Personal Arcana, was drawn in this reading.",
            })
        if code == year_code:
            signals.append({
                "type": "year_arcana_match",
                "card_code": code,
                "card_name": name,
                "message": f"{name}, the user's Year Arcana, was drawn in this reading.",
            })

    return signals
