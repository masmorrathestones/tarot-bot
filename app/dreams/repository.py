from sqlalchemy import Select, or_, select
from sqlalchemy.orm import Session

from app.dreams.models import DreamSymbolEntity


class DreamSymbolRepository:
    def search(
        self,
        db: Session,
        term: str,
        *,
        language: str = "pt",
        interpretation_type: str | None = None,
        limit: int = 20,
    ) -> list[DreamSymbolEntity]:
        clean = " ".join(term.strip().split())
        if not clean:
            return []

        name_column = {
            "pt": DreamSymbolEntity.name_pt,
            "en": DreamSymbolEntity.name_en,
            "es": DreamSymbolEntity.name_es,
        }.get(language, DreamSymbolEntity.name_pt)
        query: Select[tuple[DreamSymbolEntity]] = select(DreamSymbolEntity).where(
            DreamSymbolEntity.active.is_(True),
            or_(
                name_column.ilike(f"%{clean}%"),
                DreamSymbolEntity.name_pt.ilike(f"%{clean}%"),
                DreamSymbolEntity.name_en.ilike(f"%{clean}%"),
                DreamSymbolEntity.name_es.ilike(f"%{clean}%"),
            ),
        )
        if interpretation_type:
            query = query.where(
                DreamSymbolEntity.interpretation_type == interpretation_type.upper()
            )
        return list(db.scalars(query.order_by(name_column, DreamSymbolEntity.id).limit(limit)).all())


dream_symbol_repository = DreamSymbolRepository()
