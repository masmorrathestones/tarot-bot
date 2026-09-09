from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean, DateTime, ForeignKey, Integer, JSON, String, Text,
    UniqueConstraint, func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database.base import Base


class UserEntity(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    whatsapp_number: Mapped[str] = mapped_column(
        String(32), nullable=False, unique=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    profile: Mapped[Optional["UserProfileEntity"]] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    readings: Mapped[list["ReadingEntity"]] = relationship(
        back_populates="user"
    )
    whatsapp_conversation: Mapped[Optional["WhatsAppConversationEntity"]] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class UserProfileEntity(Base):
    __tablename__ = "user_profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, unique=True, index=True
    )
    sun_sign: Mapped[Optional[str]] = mapped_column(String(30))
    moon_sign: Mapped[Optional[str]] = mapped_column(String(30))
    rising_sign: Mapped[Optional[str]] = mapped_column(String(30))
    mbti: Mapped[Optional[str]] = mapped_column(String(10))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["UserEntity"] = relationship(back_populates="profile")


class ReadingEntity(Base):
    __tablename__ = "readings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False, index=True
    )
    deck_code: Mapped[str] = mapped_column(String(60), nullable=False)
    spread_code: Mapped[str] = mapped_column(String(80), nullable=False)
    question: Mapped[str] = mapped_column(String(500), nullable=False)
    context: Mapped[Optional[str]] = mapped_column(String(1000))
    allow_reversed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )

    profile_snapshot: Mapped[dict] = mapped_column(
        JSON, nullable=False, default=dict
    )

    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", index=True
    )
    retry_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    last_attempt_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    ai_model: Mapped[Optional[str]] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(
        String(40), nullable=False, default="v1"
    )
    knowledge_version: Mapped[str] = mapped_column(
        String(40), nullable=False, default="banzhaf-v1"
    )

    narrative: Mapped[Optional[str]] = mapped_column(Text)
    card_analysis: Mapped[Optional[str]] = mapped_column(Text)
    synthesis: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )

    user: Mapped["UserEntity"] = relationship(back_populates="readings")
    drawn_cards: Mapped[list["DrawnCardEntity"]] = relationship(
        back_populates="reading",
        cascade="all, delete-orphan",
        order_by="DrawnCardEntity.position_index",
    )


class DrawnCardEntity(Base):
    __tablename__ = "drawn_cards"
    __table_args__ = (
        UniqueConstraint(
            "reading_id", "position_index",
            name="uq_drawn_cards_reading_position"
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reading_id: Mapped[int] = mapped_column(
        ForeignKey("readings.id", ondelete="CASCADE"),
        nullable=False, index=True
    )
    card_code: Mapped[str] = mapped_column(String(80), nullable=False)
    card_name: Mapped[str] = mapped_column(String(120), nullable=False)
    position_index: Mapped[int] = mapped_column(Integer, nullable=False)
    position_code: Mapped[str] = mapped_column(String(80), nullable=False)
    position_name: Mapped[str] = mapped_column(String(120), nullable=False)
    position_description: Mapped[str] = mapped_column(
        String(500), nullable=False
    )
    orientation: Mapped[str] = mapped_column(String(20), nullable=False)

    reading: Mapped["ReadingEntity"] = relationship(
        back_populates="drawn_cards"
    )



class WhatsAppConversationEntity(Base):
    __tablename__ = "whatsapp_conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    state: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="AWAITING_QUESTION",
        index=True,
    )
    pending_question: Mapped[Optional[str]] = mapped_column(String(500))
    pending_context: Mapped[Optional[str]] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user: Mapped["UserEntity"] = relationship(
        back_populates="whatsapp_conversation"
    )


class WhatsAppMessageEventEntity(Base):
    __tablename__ = "whatsapp_message_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    whatsapp_message_id: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
    )
    from_number: Mapped[str] = mapped_column(String(32), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(120))
    message_type: Mapped[str] = mapped_column(String(30), nullable=False)
    text_body: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="RECEIVED",
        index=True,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
