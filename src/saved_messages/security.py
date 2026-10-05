import hashlib
import hmac
import secrets
from datetime import UTC, datetime, timedelta

from cryptography.fernet import Fernet, InvalidToken
from fastapi import HTTPException, Request, status
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from saved_messages.config import settings
from saved_messages.models import User, UserSession

password_hash = PasswordHash.recommended()
SESSION_COOKIE = "saved_messages_session"
SESSION_LIFETIME = timedelta(days=30)


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    return hmac.new(
        settings.app_secret_key.encode(),
        token.encode(),
        hashlib.sha256,
    ).hexdigest()


async def create_session(db: AsyncSession, user: User) -> str:
    token = new_session_token()
    db.add(
        UserSession(
            user_id=user.id,
            token_hash=token_digest(token),
            expires_at=datetime.now(UTC) + SESSION_LIFETIME,
        )
    )
    await db.commit()
    return token


async def get_current_user(request: Request, db: AsyncSession) -> User:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in required")
    result = await db.execute(
        select(User)
        .join(UserSession)
        .where(
            UserSession.token_hash == token_digest(token),
            UserSession.expires_at > datetime.now(UTC),
        )
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session expired")
    return user


def encrypt_telegram_session(value: str) -> str:
    if not settings.telegram_session_encryption_key:
        raise RuntimeError("TELEGRAM_SESSION_ENCRYPTION_KEY must be set to connect Telegram")
    return (
        Fernet(settings.telegram_session_encryption_key.encode()).encrypt(value.encode()).decode()
    )


def decrypt_telegram_session(value: str) -> str:
    if not settings.telegram_session_encryption_key:
        raise RuntimeError("TELEGRAM_SESSION_ENCRYPTION_KEY must be set to connect Telegram")
    try:
        return (
            Fernet(settings.telegram_session_encryption_key.encode())
            .decrypt(value.encode())
            .decode()
        )
    except InvalidToken as exc:
        raise RuntimeError(
            "Unable to decrypt the Telegram session; verify the encryption key"
        ) from exc
