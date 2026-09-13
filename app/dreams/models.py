from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class DreamSymbolEntity(Base):
    """One interpretive lens for a symbol that may appear in a dream.

    A canonical symbol can have more than one row because mystical and
    psychoanalytic readings must remain distinct instead of being collapsed
    into a single supposedly universal definition.
    """

    __tablename__ = "dream_symbols"
    __table_args__ = (
        CheckConstraint(
            "interpretation_type IN ('MYSTICAL', 'PSYCHOANALYTIC')",
            name="ck_dream_symbols_interpretation_type",
        ),
        UniqueConstraint(
            "canonical_key", "interpretation_type", "source_book", "source_reference",
            name="uq_dream_symbols_key_type_source",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_key: Mapped[str] = mapped_column(String(120), nullable=False, index=True)
    name_pt: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    name_en: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    name_es: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    meaning_pt: Mapped[str] = mapped_column(Text, nullable=False)
    meaning_en: Mapped[str] = mapped_column(Text, nullable=False)
    meaning_es: Mapped[str] = mapped_column(Text, nullable=False)
    interpretation_type: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    tradition: Mapped[str] = mapped_column(String(40), nullable=False)
    source_book: Mapped[str] = mapped_column(String(180), nullable=False)
    source_reference: Mapped[str] = mapped_column(String(80), nullable=False)
    context_note_pt: Mapped[str | None] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )


class DreamInterpretationEntity(Base):
    __tablename__ = "dream_interpretations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("whatsapp_conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_id: Mapped[int | None] = mapped_column(ForeignKey("tarot_payments.id", ondelete="SET NULL"), index=True)
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="pt")
    status: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    dream_text: Mapped[str] = mapped_column(Text, nullable=False)
    linguistic_analogies: Mapped[list | None] = mapped_column(JSON)
    contextual_questions: Mapped[list | None] = mapped_column(JSON)
    answers: Mapped[list | None] = mapped_column(JSON)
    current_question_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    relevant_facts: Mapped[list | None] = mapped_column(JSON)
    matched_symbols: Mapped[list | None] = mapped_column(JSON)
    final_analysis: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
