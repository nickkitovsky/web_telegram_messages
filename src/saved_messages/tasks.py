import logging
from typing import Any

from sqlalchemy import select
from taskiq import TaskiqScheduler
from taskiq.schedule_sources import LabelScheduleSource
from taskiq_redis import RedisStreamBroker
from telethon import TelegramClient
from telethon.utils import get_display_name

from saved_messages.config import settings
from saved_messages.db import SessionLocal
from saved_messages.llm import classify
from saved_messages.media import download_message_media, is_downloadable_media, media_metadata
from saved_messages.models import SavedMessage, Tag, TelegramAuth
from saved_messages.telegram import (
    get_client,
    get_message_author,
    message_payload,
    serialize_message_entities,
)

logger = logging.getLogger(__name__)
broker = RedisStreamBroker(url=settings.redis_url)
scheduler = TaskiqScheduler(broker=broker, sources=[LabelScheduleSource(broker)])
TELEGRAM_BATCH_SIZE = 50


async def fetch_saved_messages(
    client: TelegramClient, before_telegram_id: int | None = None
) -> list[Any]:
    options = {"limit": TELEGRAM_BATCH_SIZE}
    if before_telegram_id is not None:
        options["offset_id"] = before_telegram_id
    return [message async for message in client.iter_messages("me", **options)]


@broker.task
async def sync_telegram_user(user_id: int, before_telegram_id: int | None = None) -> int:
    async with SessionLocal() as db:
        auth = await db.get(TelegramAuth, user_id)
        if auth is None or auth.connected_at is None:
            return 0
        client = await get_client(auth)
        try:
            telegram_messages = await fetch_saved_messages(client, before_telegram_id)
            own_name = get_display_name(await client.get_me()) or "Вы"
            author_cache: dict[str, str] = {}
            auth.sync_has_more = len(telegram_messages) == TELEGRAM_BATCH_SIZE
            existing_messages = await db.scalars(
                select(SavedMessage).where(
                    SavedMessage.user_id == user_id,
                    SavedMessage.telegram_message_id.in_(
                        [message.id for message in telegram_messages]
                    ),
                )
            )
            existing_by_telegram_id = {
                message.telegram_message_id: message for message in existing_messages.all()
            }
            added = 0
            for telegram_message in telegram_messages:
                saved_message = existing_by_telegram_id.get(telegram_message.id)
                author_name = await get_message_author(
                    client, telegram_message, own_name, author_cache
                )
                if saved_message is None:
                    payload = message_payload(telegram_message)
                    payload["channel"] = author_name
                    saved_message = SavedMessage(user_id=user_id, **payload)
                    db.add(saved_message)
                    added += 1
                else:
                    saved_message.telegram_grouped_id = telegram_message.grouped_id
                    saved_message.text = telegram_message.message or ""
                    saved_message.text_entities = serialize_message_entities(telegram_message)
                    saved_message.channel = author_name
                    saved_message.is_forwarded = (
                        getattr(telegram_message, "fwd_from", None) is not None
                    )
                if is_downloadable_media(telegram_message) and not saved_message.media_path:
                    mime_type, kind, file_name = media_metadata(telegram_message)
                    saved_message.media_mime_type = mime_type
                    saved_message.media_kind = kind
                    saved_message.media_file_name = file_name[:255] or None
                    try:
                        media = await download_message_media(client, telegram_message, user_id)
                    except (OSError, TimeoutError, ValueError) as exc:
                        logger.warning(
                            "Could not download Telegram media for message %s: %s",
                            telegram_message.id,
                            exc,
                            exc_info=True,
                        )
                    else:
                        if media is not None:
                            saved_message.media_path = media.path
                            saved_message.media_mime_type = media.mime_type
                            saved_message.media_file_name = media.file_name
                            saved_message.media_kind = media.kind
                            saved_message.media_checked = True
                else:
                    saved_message.media_checked = True
            await db.commit()
            result = await db.scalars(
                select(SavedMessage.id)
                .where(
                    SavedMessage.user_id == user_id, SavedMessage.classification_pending.is_(True)
                )
                .order_by(SavedMessage.message_date)
            )
            for message_id in result.all():
                await classify_saved_message.kiq(message_id)
            return added
        finally:
            await client.disconnect()


@broker.task
async def hydrate_saved_message_media(user_id: int, telegram_message_ids: list[int]) -> int:
    async with SessionLocal() as db:
        auth = await db.get(TelegramAuth, user_id)
        if auth is None or auth.connected_at is None:
            return 0
        saved_messages = await db.scalars(
            select(SavedMessage).where(
                SavedMessage.user_id == user_id,
                SavedMessage.telegram_message_id.in_(telegram_message_ids),
            )
        )
        saved_by_telegram_id = {
            message.telegram_message_id: message for message in saved_messages.all()
        }
        if not saved_by_telegram_id:
            return 0

        client = await get_client(auth)
        checked = 0
        try:
            remote_messages = await client.get_messages("me", ids=list(saved_by_telegram_id))
            if not isinstance(remote_messages, list):
                remote_messages = [remote_messages] if remote_messages is not None else []
            remote_by_id = {
                message.id: message for message in remote_messages if message is not None
            }
            for telegram_id, saved_message in saved_by_telegram_id.items():
                remote_message = remote_by_id.get(telegram_id)
                if remote_message is None or not is_downloadable_media(remote_message):
                    saved_message.media_checked = True
                    checked += 1
                    continue
                mime_type, kind, file_name = media_metadata(remote_message)
                saved_message.media_mime_type = mime_type
                saved_message.media_kind = kind
                saved_message.media_file_name = file_name[:255] or None
                try:
                    media = await download_message_media(client, remote_message, user_id)
                except (OSError, TimeoutError, ValueError) as exc:
                    logger.warning(
                        "Could not hydrate Telegram media for message %s: %s",
                        telegram_id,
                        exc,
                        exc_info=True,
                    )
                    continue
                if media is not None:
                    saved_message.media_path = media.path
                    saved_message.media_mime_type = media.mime_type
                    saved_message.media_file_name = media.file_name
                    saved_message.media_kind = media.kind
                    saved_message.media_checked = True
                    checked += 1
            await db.commit()
            return checked
        finally:
            await client.disconnect()


@broker.task
async def classify_saved_message(message_id: int) -> None:
    async with SessionLocal() as db:
        message = await db.get(SavedMessage, message_id)
        if message is None or not message.classification_pending or not message.text.strip():
            if message is not None:
                message.classification_pending = False
                await db.commit()
            return
        existing = await db.scalars(select(Tag.name).where(Tag.user_id == message.user_id))
        prediction = await classify(message.text, list(existing.all()))
        message.title = prediction.title
        message.classification_confidence = prediction.confidence
        message.classification_candidates = prediction.candidates
        if prediction.tags:
            known = await db.scalars(
                select(Tag).where(Tag.user_id == message.user_id, Tag.name.in_(prediction.tags))
            )
            tags_by_name = {tag.name: tag for tag in known.all()}
            message.tags = []
            for name in prediction.tags:
                tag = tags_by_name.get(name)
                if tag is None:
                    tag = Tag(user_id=message.user_id, name=name)
                    db.add(tag)
                message.tags.append(tag)
        message.classification_pending = False
        await db.commit()


@broker.task(schedule=[{"cron": "*/15 * * * *"}])
async def enqueue_connected_user_syncs() -> int:
    async with SessionLocal() as db:
        result = await db.scalars(
            select(TelegramAuth.user_id).where(TelegramAuth.connected_at.is_not(None))
        )
        user_ids = result.all()
    for user_id in user_ids:
        await sync_telegram_user.kiq(user_id)
    return len(user_ids)


@broker.task
async def enqueue_user_sync(user_id: int) -> None:
    await sync_telegram_user.kiq(user_id)
