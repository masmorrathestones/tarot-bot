from __future__ import annotations

import re
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dreams.models import DreamSymbolEntity


def normalize_words(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value.casefold())
    without_marks = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", without_marks))


def match_dream_symbols(db: Session, dream_text: str, *, language: str) -> list[dict]:
    dream = f" {normalize_words(dream_text)} "
    rows = list(db.scalars(select(DreamSymbolEntity).where(DreamSymbolEntity.active.is_(True))))
    matches: list[tuple[int, int, DreamSymbolEntity, str]] = []
    for row in rows:
        names = {row.name_pt, row.name_en, row.name_es}
        for name in names:
            normalized = normalize_words(name)
            if normalized and f" {normalized} " in dream:
                matches.append((len(normalized.split()), len(normalized), row, name))
                break
    matches.sort(key=lambda item: (-item[0], -item[1], item[2].id))
    meaning_attr = f"meaning_{language}" if language in {"pt", "en", "es"} else "meaning_pt"
    name_attr = f"name_{language}" if language in {"pt", "en", "es"} else "name_pt"
    return [{
        "symbol_id": row.id,
        "canonical_key": row.canonical_key,
        "name": getattr(row, name_attr),
        "matched_as": matched,
        "meaning": getattr(row, meaning_attr),
        "interpretation_type": row.interpretation_type,
        "source_book": row.source_book,
        "source_reference": row.source_reference,
    } for _, _, row, matched in matches]
