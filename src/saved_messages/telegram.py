import re
from datetime import datetime
from typing import Any
from urllib.parse import unquote, urlparse

from fastapi import HTTPException
from python_socks import ProxyType
from sqlalchemy.ext.asyncio import AsyncSession
from telethon import TelegramClient
from telethon.errors import RPCError, SessionPasswordNeededError
from telethon.sessions import StringSession
from telethon.utils import get_display_name

from saved_messages.config import settings
from saved_messages.models import TelegramAuth
from saved_messages.security import decrypt_telegram_session, encrypt_telegram_session


def _client(session: str = "") -> TelegramClient:
    if settings.telegram_api_id is None or not settings.telegram_api_hash:
        raise RuntimeError("Set TELEGRAM_API_ID and TELEGRAM_API_HASH before connecting Telegram")
    proxy = parse_proxy_url(settings.telegram_proxy_url) if settings.telegram_proxy_url else None
    return TelegramClient(
        StringSession(session),
        settings.telegram_api_id,
        settings.telegram_api_hash,
        proxy=proxy,
        timeout=15,
        connection_retries=1,
        request_retries=1,
        retry_delay=1,
    )


def parse_proxy_url(url: str) -> dict[str, object]:
    parsed = urlparse(url)
    proxy_types = {
        "socks5": ProxyType.SOCKS5,
        "socks4": ProxyType.SOCKS4,
        "http": ProxyType.HTTP,
    }
    if parsed.scheme not in proxy_types or not parsed.hostname or parsed.port is None:
        raise ValueError(
            "TELEGRAM_PROXY_URL must be a socks5://, socks4://, or http:// URL with a host and port"
        )
    proxy: dict[str, object] = {
        "proxy_type": proxy_types[parsed.scheme],
        "addr": parsed.hostname,
        "port": parsed.port,
        "rdns": True,
    }
    if parsed.username is not None:
        proxy["username"] = unquote(parsed.username)
    if parsed.password is not None:
        proxy["password"] = unquote(parsed.password)
    return proxy


async def start_login(db: AsyncSession, auth: TelegramAuth, phone: str) -> None:
    client = _client()
    try:
        await client.connect()
        sent = await client.send_code_request(phone)
        auth.encrypted_session = encrypt_telegram_session(client.session.save())
        auth.pending_phone = phone
        auth.phone_code_hash = sent.phone_code_hash
        auth.password_required = False
        await db.commit()
    finally:
        await client.disconnect()


async def submit_code(db: AsyncSession, auth: TelegramAuth, code: str) -> bool:
    if not auth.encrypted_session or not auth.pending_phone or not auth.phone_code_hash:
        raise HTTPException(status_code=409, detail="Start Telegram login before submitting a code")
    client = _client(decrypt_telegram_session(auth.encrypted_session))
    try:
        await client.connect()
        try:
            await client.sign_in(auth.pending_phone, code, phone_code_hash=auth.phone_code_hash)
        except SessionPasswordNeededError:
            auth.encrypted_session = encrypt_telegram_session(client.session.save())
            auth.password_required = True
            await db.commit()
            return False
        await _complete_login(db, auth, client)
        return True
    finally:
        await client.disconnect()


async def submit_password(db: AsyncSession, auth: TelegramAuth, password: str) -> None:
    if not auth.encrypted_session or not auth.password_required:
        raise HTTPException(status_code=409, detail="Telegram is not waiting for a password")
    client = _client(decrypt_telegram_session(auth.encrypted_session))
    try:
        await client.connect()
        await client.sign_in(password=password)
        await _complete_login(db, auth, client)
    finally:
        await client.disconnect()


async def _complete_login(db: AsyncSession, auth: TelegramAuth, client: TelegramClient) -> None:
    from datetime import UTC

    auth.encrypted_session = encrypt_telegram_session(client.session.save())
    auth.pending_phone = None
    auth.phone_code_hash = None
    auth.password_required = False
    auth.connected_at = datetime.now(UTC)
    await db.commit()


async def get_client(auth: TelegramAuth) -> TelegramClient:
    if not auth.encrypted_session or auth.connected_at is None:
        raise HTTPException(status_code=409, detail="Connect a Telegram account first")
    client = _client(decrypt_telegram_session(auth.encrypted_session))
    try:
        await client.connect()
    except ConnectionError, OSError, TimeoutError:
        await client.disconnect()
        raise
    if not await client.is_user_authorized():
        await client.disconnect()
        raise HTTPException(status_code=401, detail="Telegram session is no longer authorized")
    return client


async def get_telegram_auth(
    db: AsyncSession, user_id: int, *, create: bool = False
) -> TelegramAuth:
    from sqlalchemy import select

    result = await db.execute(select(TelegramAuth).where(TelegramAuth.user_id == user_id))
    auth = result.scalar_one_or_none()
    if auth is None and create:
        auth = TelegramAuth(user_id=user_id)
        db.add(auth)
        await db.flush()
    if auth is None:
        raise HTTPException(status_code=409, detail="Connect a Telegram account first")
    return auth


def message_payload(message: Any) -> dict[str, Any]:
    text = message.message or ""
    return {
        "telegram_message_id": message.id,
        "telegram_grouped_id": message.grouped_id,
        "text": text,
        "text_entities": serialize_message_entities(message),
        "title": None,
        "message_date": message.date or datetime.now().astimezone(),
        "channel": None,
        "is_forwarded": getattr(message, "fwd_from", None) is not None,
        "archived": False,
        "classification_pending": True,
    }


async def get_message_author(
    client: TelegramClient,
    message: Any,
    own_name: str,
    cache: dict[str, str] | None = None,
) -> str:
    forward = getattr(message, "fwd_from", None)
    if forward is None:
        return own_name

    fallback = (
        getattr(forward, "from_name", None)
        or getattr(message, "post_author", None)
        or "Источник пересылки"
    )
    peer = getattr(forward, "from_id", None)
    if peer is None:
        return str(fallback)

    peer_key = str(peer)
    if cache is not None and peer_key in cache:
        return cache[peer_key]
    try:
        source = await client.get_entity(peer)
    except ValueError, RPCError:
        return str(fallback)

    display_name = getattr(source, "title", None) or get_display_name(source) or fallback
    result = str(display_name)
    if cache is not None:
        cache[peer_key] = result
    return result


def serialize_message_entities(message: Any) -> list[dict[str, object]]:
    serialized = []
    for entity in getattr(message, "entities", None) or ():
        entity_type = entity.__class__.__name__
        if entity_type.startswith("MessageEntity"):
            entity_type = entity_type.removeprefix("MessageEntity")
        entity_type = _camel_to_snake(entity_type)
        item: dict[str, object] = {
            "type": entity_type,
            "offset": int(entity.offset),
            "length": int(entity.length),
        }
        url = getattr(entity, "url", None)
        language = getattr(entity, "language", None)
        if url:
            item["url"] = str(url)
        if language:
            item["language"] = str(language)
        serialized.append(item)
    return serialized


def _camel_to_snake(value: str) -> str:
    return re.sub(r"(?<!^)(?=[A-Z])", "_", value).lower()
