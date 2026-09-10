from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, Time,
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
    birth_date: Mapped[Optional[date]] = mapped_column(Date())
    birth_time: Mapped[Optional[time]] = mapped_column(Time())
    birth_place: Mapped[Optional[str]] = mapped_column(String(250))
    birth_latitude: Mapped[Optional[float]] = mapped_column(Float())
    birth_longitude: Mapped[Optional[float]] = mapped_column(Float())
    birth_timezone: Mapped[Optional[str]] = mapped_column(String(80))
    natal_chart: Mapped[Optional[dict]] = mapped_column(JSON)
    zodiac_sign: Mapped[Optional[str]] = mapped_column(String(30))
    personal_number: Mapped[Optional[int]] = mapped_column(Integer)
    personal_arcana_number: Mapped[Optional[int]] = mapped_column(Integer)
    personal_arcana_name: Mapped[Optional[str]] = mapped_column(String(120))
    year_arcana_number: Mapped[Optional[int]] = mapped_column(Integer)
    year_arcana_name: Mapped[Optional[str]] = mapped_column(String(120))
    year_arcana_reference_year: Mapped[Optional[int]] = mapped_column(Integer)
    profile_analysis: Mapped[Optional[str]] = mapped_column(Text)
    profile_analysis_summary: Mapped[Optional[str]] = mapped_column(Text)
    profile_analysis_reference_year: Mapped[Optional[int]] = mapped_column(Integer)
    profile_analysis_created_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
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
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        unique=True,
        index=True,
    )
    whatsapp_number: Mapped[str] = mapped_column(
        String(32), nullable=False, unique=True, index=True
    )
    state: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        default="AWAITING_QUESTION",
        index=True,
    )
    language: Mapped[str] = mapped_column(String(5), nullable=False, default="en")
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

    user: Mapped[Optional["UserEntity"]] = relationship(
        back_populates="whatsapp_conversation"
    )


class TarotPaymentEntity(Base):
    __tablename__ = "tarot_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("whatsapp_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    provider: Mapped[str] = mapped_column(String(20), nullable=False, default="stripe")
    provider_session_id: Mapped[str] = mapped_column(
        String(255), nullable=False, unique=True, index=True
    )
    checkout_choice_token: Mapped[Optional[str]] = mapped_column(
        String(64), nullable=True, unique=True, index=True
    )
    checkout_url: Mapped[str] = mapped_column(Text, nullable=False)
    amount_cents: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="usd")
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="PENDING", index=True
    )
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
        server_default=func.now(), onupdate=func.now()
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


class WhatsAppOutboundMessageEntity(Base):
    __tablename__ = "whatsapp_outbound_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    whatsapp_message_id: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
        index=True,
    )
    to_number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    text_body: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACCEPTED",
        index=True,
    )
    provider_status: Mapped[Optional[str]] = mapped_column(String(30))
    error_code: Mapped[Optional[int]] = mapped_column(Integer)
    error_title: Mapped[Optional[str]] = mapped_column(String(500))
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    status_updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
