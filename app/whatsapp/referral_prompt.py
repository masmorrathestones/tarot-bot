from __future__ import annotations

import random
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.feature_models import RuntimeSettingEntity
from app.whatsapp.i18n import normalize_language


_MESSAGES = {
    "pt": (
        "🔮 Se essa experiência te lembrou alguém que também curtiria uma tiragem, compartilhe o Holomancy com essa pessoa: https://wa.me/5521992283542",
        "✨ Conhece alguém que gostaria de uma leitura de Tarô mais completa? Se quiser, compartilhe o Holomancy: https://wa.me/5521992283542",
        "🌙 Se algum amigo seu também curte Tarô, manda o Holomancy pra ele: https://wa.me/5521992283542",
    ),
    "en": (
        "🔮 If this experience made you think of someone who would enjoy a reading too, feel free to share Holomancy: https://wa.me/5521992283542",
        "✨ Know someone who might enjoy a deeper Tarot reading? You can share Holomancy with them: https://wa.me/5521992283542",
        "🌙 If a friend of yours is into Tarot too, send them Holomancy: https://wa.me/5521992283542",
    ),
    "es": (
        "🔮 Si esta experiencia te hizo pensar en alguien que también disfrutaría una tirada, comparte Holomancy: https://wa.me/5521992283542",
        "✨ ¿Conoces a alguien a quien le gustaría una lectura de Tarot más completa? Puedes compartir Holomancy: https://wa.me/5521992283542",
        "🌙 Si algún amigo tuyo también disfruta del Tarot, envíale Holomancy: https://wa.me/5521992283542",
    ),
}


def maybe_daily_referral_prompt(db: Session, language: str) -> str | None:
    """Return at most one share prompt per UTC day, attached to an active user interaction."""
    today = datetime.now(timezone.utc).date().isoformat()
    row = db.scalar(
        select(RuntimeSettingEntity)
        .where(RuntimeSettingEntity.key == "daily_referral_prompt_date")
        .with_for_update()
    )
    if row is None:
        row = RuntimeSettingEntity(key="daily_referral_prompt_date", value="")
        db.add(row)
        db.flush()
    if row.value == today:
        return None

    now_hour = datetime.now(timezone.utc).hour
    probability = 1.0 if now_hour >= 20 else 0.35
    if random.random() > probability:
        db.commit()
        return None

    language = normalize_language(language)
    row.value = today
    db.commit()
    return random.choice(_MESSAGES[language])
