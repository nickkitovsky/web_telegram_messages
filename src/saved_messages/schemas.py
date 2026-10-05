from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Credentials(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=256)


class UserView(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr


class TelegramPhone(BaseModel):
    phone: str = Field(min_length=5, max_length=32)


class TelegramCode(BaseModel):
    code: str = Field(min_length=1, max_length=16)


class TelegramPassword(BaseModel):
    password: str = Field(min_length=1, max_length=256)


class MessageUpdate(BaseModel):
    title: str | None = Field(default=None, max_length=240)
    tags: list[str] | None = Field(default=None, max_length=20)
    archived: bool | None = None


class MessageMediaRequest(BaseModel):
    message_ids: list[int] = Field(min_length=1, max_length=1000)


class MessageMediaView(BaseModel):
    message_id: int
    media_url: str | None
    media_mime_type: str | None
    media_file_name: str | None
    media_kind: str | None
    media_checked: bool


class MessageTextEntity(BaseModel):
    type: str
    offset: int
    length: int
    url: str | None = None
    language: str | None = None


class MessageView(BaseModel):
    id: int
    telegram_message_id: int
    telegram_message_ids: list[int]
    message_ids: list[int]
    text: str
    text_entities: list[MessageTextEntity]
    title: str | None
    message_date: datetime
    channel: str | None
    is_forwarded: bool
    tags: list[str]
    archived: bool
    classification_confidence: float | None
    classification_candidates: list[str]
    media_url: str | None
    media_mime_type: str | None
    media_file_name: str | None
    media_kind: str | None
    media_checked: bool
    media_files: list[MessageMediaView]
