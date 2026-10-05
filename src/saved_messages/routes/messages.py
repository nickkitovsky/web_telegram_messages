from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.responses import FileResponse
from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from saved_messages.config import settings
from saved_messages.db import get_db
from saved_messages.dependencies import authenticated_user
from saved_messages.media import download_message_media
from saved_messages.models import SavedMessage, Tag, TelegramAuth, User
from saved_messages.schemas import MessageMediaView, MessageTextEntity, MessageUpdate, MessageView
from saved_messages.telegram import get_client

router = APIRouter(tags=["messages"])


def as_view(group: list[SavedMessage]) -> MessageView:
    message = group[0]
    tags = list(dict.fromkeys(tag.name for item in group for tag in item.tags))
    candidates = list(
        dict.fromkeys(candidate for item in group for candidate in item.classification_candidates)
    )
    media_files = [
        MessageMediaView(
            message_id=item.id,
            media_url=f"/messages/{item.id}/media" if item.media_mime_type else None,
            media_mime_type=item.media_mime_type,
            media_file_name=item.media_file_name,
            media_kind=item.media_kind,
            media_checked=item.media_checked,
        )
        for item in group
        if item.media_mime_type or item.media_path or item.media_checked is False
    ]
    captions = [item.text for item in group if item.text]
    text_parts: list[str] = []
    text_entities: list[MessageTextEntity] = []
    cursor = 0
    for item in group:
        part = item.text
        if not part:
            continue
        if text_parts:
            text_parts.append("\n")
            cursor += 1
        text_parts.append(part)
        for entity in item.text_entities or []:
            text_entities.append(
                MessageTextEntity(
                    **{
                        **entity,
                        "offset": int(entity["offset"]) + cursor,
                    }
                )
            )
        cursor += len(part.encode("utf-16-le")) // 2
    title = next((item.title for item in group if item.title), None)
    confidences = [
        item.classification_confidence
        for item in group
        if item.classification_confidence is not None
    ]
    first_media = next((item for item in media_files if item.media_url), None)
    return MessageView(
        id=message.id,
        telegram_message_id=message.telegram_message_id,
        telegram_message_ids=[item.telegram_message_id for item in group],
        message_ids=[item.id for item in group],
        text="".join(text_parts) if text_parts else "\n".join(captions),
        text_entities=text_entities,
        title=title,
        message_date=message.message_date,
        channel=message.channel,
        is_forwarded=any(item.is_forwarded for item in group),
        tags=tags,
        archived=any(item.archived for item in group),
        classification_confidence=min(confidences) if confidences else None,
        classification_candidates=candidates,
        media_url=first_media.media_url if first_media else None,
        media_mime_type=first_media.media_mime_type if first_media else None,
        media_file_name=first_media.media_file_name if first_media else None,
        media_kind=first_media.media_kind if first_media else None,
        media_checked=all(item.media_checked for item in group),
        media_files=media_files,
    )


@router.get("/messages", response_model=list[MessageView])
async def list_messages(
    response: Response,
    q: str | None = Query(default=None, max_length=300),
    tag: str | None = Query(default=None, max_length=80),
    include_archived: bool = False,
    archived_only: bool = False,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> list[MessageView]:
    conditions = [SavedMessage.user_id == user.id]
    if archived_only:
        conditions.append(SavedMessage.archived.is_(True))
    elif not include_archived:
        conditions.append(SavedMessage.archived.is_(False))
    if q:
        pattern = f"%{q}%"
        conditions.append(
            or_(
                SavedMessage.text.ilike(pattern),
                SavedMessage.title.ilike(pattern),
                SavedMessage.channel.ilike(pattern),
                SavedMessage.tags.any(Tag.name.ilike(pattern)),
            )
        )
    if tag:
        conditions.append(SavedMessage.tags.any(Tag.name == tag.strip().lower()))

    group_key = case(
        (SavedMessage.telegram_grouped_id.is_not(None), SavedMessage.telegram_grouped_id),
        else_=-SavedMessage.id,
    )
    page_result = await db.execute(
        select(group_key.label("group_key"), func.max(SavedMessage.message_date).label("date"))
        .where(*conditions)
        .group_by(group_key)
        .order_by(func.max(SavedMessage.message_date).desc(), group_key.desc())
        .limit(limit + 1)
        .offset(offset)
    )
    page_keys = [row.group_key for row in page_result.all()]
    has_local_next = len(page_keys) > limit
    page_keys = page_keys[:limit]

    single_message_ids = [-key for key in page_keys if key < 0]
    album_ids = [key for key in page_keys if key > 0]
    if single_message_ids or album_ids:
        item_condition = or_(
            SavedMessage.id.in_(single_message_ids) if single_message_ids else False,
            SavedMessage.telegram_grouped_id.in_(album_ids) if album_ids else False,
        )
        result = await db.scalars(
            select(SavedMessage)
            .options(selectinload(SavedMessage.tags))
            .where(SavedMessage.user_id == user.id, item_condition)
            .order_by(SavedMessage.message_date.desc(), SavedMessage.id.desc())
        )
        grouped_messages: dict[int, list[SavedMessage]] = {}
        for item in result.all():
            key = item.telegram_grouped_id if item.telegram_grouped_id is not None else -item.id
            grouped_messages.setdefault(key, []).append(item)
        page = [grouped_messages[key] for key in page_keys]
    else:
        page = []

    auth = await db.get(TelegramAuth, user.id)
    response.headers["X-Has-Next"] = str(
        has_local_next or (not archived_only and bool(auth and auth.sync_has_more))
    ).lower()
    response.headers["X-Has-Previous"] = str(offset > 0).lower()
    oldest_telegram_id = await db.scalar(
        select(func.min(SavedMessage.telegram_message_id)).where(SavedMessage.user_id == user.id)
    )
    if oldest_telegram_id is not None:
        response.headers["X-Older-Telegram-ID"] = str(oldest_telegram_id)
    return [as_view(group) for group in page]


@router.get("/messages/{message_id}/media")
async def get_message_media(
    message_id: int,
    user: User = Depends(authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    message = await db.scalar(
        select(SavedMessage).where(
            SavedMessage.id == message_id,
            SavedMessage.user_id == user.id,
        )
    )
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    media_path = _stored_media_path(message.media_path)
    if media_path is None or not media_path.is_file():
        client = await get_client(await _get_telegram_auth(db, user.id))
        try:
            remote_message = await client.get_messages("me", ids=message.telegram_message_id)
            if remote_message is None:
                raise HTTPException(status_code=404, detail="Telegram media message was not found")
            downloaded = await download_message_media(client, remote_message, user.id)
        except (ConnectionError, OSError, TimeoutError) as exc:
            raise HTTPException(
                status_code=503, detail="Could not download this media from Telegram"
            ) from exc
        finally:
            await client.disconnect()
        if downloaded is None:
            raise HTTPException(status_code=404, detail="This message has no downloadable media")
        message.media_path = downloaded.path
        message.media_mime_type = downloaded.mime_type
        message.media_file_name = downloaded.file_name
        message.media_kind = downloaded.kind
        await db.commit()
        media_path = _stored_media_path(message.media_path)
        if media_path is None or not media_path.is_file():
            raise HTTPException(status_code=404, detail="Downloaded media file is missing")

    return FileResponse(
        media_path,
        media_type=message.media_mime_type or "application/octet-stream",
        filename=message.media_file_name or media_path.name,
        content_disposition_type="inline",
    )


def _stored_media_path(relative_path: str | None) -> Path | None:
    if not relative_path:
        return None
    media_root = Path(settings.media_storage_path).resolve()
    media_path = (media_root / relative_path).resolve()
    if not media_path.is_relative_to(media_root):
        return None
    return media_path


async def _get_telegram_auth(db: AsyncSession, user_id: int) -> TelegramAuth:
    auth = await db.get(TelegramAuth, user_id)
    if auth is None or auth.connected_at is None:
        raise HTTPException(status_code=409, detail="Connect a Telegram account to download media")
    return auth


@router.patch("/messages/{message_id}", response_model=MessageView)
async def update_message(
    message_id: int,
    payload: MessageUpdate,
    user: User = Depends(authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> MessageView:
    message = await db.scalar(
        select(SavedMessage).where(SavedMessage.id == message_id, SavedMessage.user_id == user.id)
    )
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    group = await _get_message_group(db, user.id, message)
    if payload.title is not None:
        title = payload.title.strip() or None
        for item in group:
            item.title = title
    if payload.archived is not None:
        for item in group:
            item.archived = payload.archived
    if payload.tags is not None:
        names = list(dict.fromkeys(name.strip().lower() for name in payload.tags if name.strip()))
        if any(len(name) > 80 for name in names):
            raise HTTPException(status_code=422, detail="Tag names must be at most 80 characters")
        found = await db.scalars(select(Tag).where(Tag.user_id == user.id, Tag.name.in_(names)))
        tags_by_name = {tag.name: tag for tag in found.all()}
        tags = []
        for name in names:
            tag = tags_by_name.get(name)
            if tag is None:
                tag = Tag(user_id=user.id, name=name)
                db.add(tag)
                tags_by_name[name] = tag
            tags.append(tag)
        for item in group:
            item.tags = tags
    await db.commit()
    updated_group = await _get_message_group(db, user.id, message)
    return as_view(updated_group)


@router.delete("/messages/{message_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_message(
    message_id: int,
    user: User = Depends(authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> Response:
    message = await db.scalar(
        select(SavedMessage).where(SavedMessage.id == message_id, SavedMessage.user_id == user.id)
    )
    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")
    group = await _get_message_group(db, user.id, message)
    auth = await db.get(TelegramAuth, user.id)
    if auth is None:
        raise HTTPException(
            status_code=409, detail="Connect Telegram to delete the original message"
        )
    client = await get_client(auth)
    try:
        await client.delete_messages("me", [item.telegram_message_id for item in group])
    finally:
        await client.disconnect()
    for item in group:
        await db.delete(item)
    await db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


async def _get_message_group(
    db: AsyncSession, user_id: int, message: SavedMessage
) -> list[SavedMessage]:
    statement = (
        select(SavedMessage)
        .options(selectinload(SavedMessage.tags))
        .where(SavedMessage.user_id == user_id)
    )
    if message.telegram_grouped_id is None:
        statement = statement.where(SavedMessage.id == message.id)
    else:
        statement = statement.where(SavedMessage.telegram_grouped_id == message.telegram_grouped_id)
    result = await db.scalars(statement.order_by(SavedMessage.message_date.desc()))
    return result.all()


@router.get("/tags", response_model=list[dict[str, int | str]])
async def list_tags(
    user: User = Depends(authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, int | str]]:
    result = await db.execute(
        select(Tag.name, func.count(SavedMessage.id))
        .join(Tag.messages)
        .where(Tag.user_id == user.id)
        .group_by(Tag.name)
        .order_by(Tag.name)
    )
    return [{"name": name, "count": count} for name, count in result.all()]
