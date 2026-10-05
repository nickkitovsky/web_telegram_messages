from datetime import datetime

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from saved_messages.db import Base

message_tags = Table(
    "saved_message_tags",
    Base.metadata,
    Column("message_id", ForeignKey("saved_messages.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sessions: Mapped[list[UserSession]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    messages: Mapped[list[SavedMessage]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class UserSession(Base):
    __tablename__ = "user_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    user: Mapped[User] = relationship(back_populates="sessions")


class TelegramAuth(Base):
    __tablename__ = "telegram_auth"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    encrypted_session: Mapped[str | None] = mapped_column(Text)
    pending_phone: Mapped[str | None] = mapped_column(String(32))
    phone_code_hash: Mapped[str | None] = mapped_column(Text)
    password_required: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    connected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_has_more: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_tags_user_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    messages: Mapped[list[SavedMessage]] = relationship(
        secondary=message_tags, back_populates="tags"
    )


class SavedMessage(Base):
    __tablename__ = "saved_messages"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "telegram_message_id", name="uq_saved_messages_user_telegram_id"
        ),
        Index("ix_saved_messages_user_date", "user_id", "message_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    telegram_message_id: Mapped[int] = mapped_column(BigInteger)
    telegram_grouped_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    text: Mapped[str] = mapped_column(Text, default="", server_default="")
    text_entities: Mapped[list[dict[str, object]]] = mapped_column(
        JSONB, default=list, server_default="[]"
    )
    title: Mapped[str | None] = mapped_column(String(240))
    message_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    channel: Mapped[str | None] = mapped_column(String(255))
    is_forwarded: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    archived: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    classification_confidence: Mapped[float | None]
    classification_candidates: Mapped[list[str]] = mapped_column(
        JSON, default=list, server_default="[]"
    )
    classification_pending: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default="true"
    )
    media_path: Mapped[str | None] = mapped_column(String(500))
    media_mime_type: Mapped[str | None] = mapped_column(String(120))
    media_file_name: Mapped[str | None] = mapped_column(String(255))
    media_kind: Mapped[str | None] = mapped_column(String(32))
    media_checked: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    user: Mapped[User] = relationship(back_populates="messages")
    tags: Mapped[list[Tag]] = relationship(secondary=message_tags, back_populates="messages")
