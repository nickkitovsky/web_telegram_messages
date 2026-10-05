from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from telethon.errors import (
    FloodWaitError,
    PasswordHashInvalidError,
    PhoneCodeExpiredError,
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
)

from saved_messages.db import get_db
from saved_messages.dependencies import authenticated_user
from saved_messages.models import TelegramAuth, User
from saved_messages.schemas import TelegramCode, TelegramPassword, TelegramPhone
from saved_messages.telegram import get_telegram_auth, start_login, submit_code, submit_password

router = APIRouter(prefix="/telegram", tags=["telegram"])


@router.post("/start")
async def begin_telegram_login(
    payload: TelegramPhone,
    user: User = Depends(authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    auth = await get_telegram_auth(db, user.id, create=True)
    try:
        await start_login(db, auth, payload.phone)
    except PhoneNumberInvalidError as exc:
        raise HTTPException(status_code=422, detail="Telegram rejected this phone number") from exc
    except FloodWaitError as exc:
        raise HTTPException(
            status_code=429, detail=f"Telegram rate limited login for {exc.seconds} seconds"
        ) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (ConnectionError, OSError, TimeoutError) as exc:
        raise HTTPException(
            status_code=503,
            detail=(
                "Could not establish a connection to Telegram. The network, ISP, or VPN may be "
                "resetting Telegram's MTProto connection. Try another network or configure "
                "TELEGRAM_PROXY_URL (for example, a reachable SOCKS5 proxy), then restart "
                "the application."
            ),
        ) from exc
    return {"status": "code_sent"}


@router.post("/code")
async def telegram_code(
    payload: TelegramCode,
    user: User = Depends(authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | bool]:
    auth = await get_telegram_auth(db, user.id)
    try:
        authorized = await submit_code(db, auth, payload.code)
    except (PhoneCodeInvalidError, PhoneCodeExpiredError) as exc:
        raise HTTPException(status_code=422, detail="Telegram code is invalid or expired") from exc
    except FloodWaitError as exc:
        raise HTTPException(
            status_code=429, detail=f"Telegram rate limited login for {exc.seconds} seconds"
        ) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (ConnectionError, OSError, TimeoutError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not reconnect to Telegram. Check the network or TELEGRAM_PROXY_URL.",
        ) from exc
    return {
        "status": "connected" if authorized else "password_required",
        "authorized": authorized,
        "password_required": not authorized,
    }


@router.post("/password")
async def telegram_password(
    payload: TelegramPassword,
    user: User = Depends(authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    auth = await get_telegram_auth(db, user.id)
    try:
        await submit_password(db, auth, payload.password)
    except PasswordHashInvalidError as exc:
        raise HTTPException(status_code=422, detail="Telegram password is incorrect") from exc
    except FloodWaitError as exc:
        raise HTTPException(
            status_code=429, detail=f"Telegram rate limited login for {exc.seconds} seconds"
        ) from exc
    except (RuntimeError, ValueError) as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (ConnectionError, OSError, TimeoutError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Could not reconnect to Telegram. Check the network or TELEGRAM_PROXY_URL.",
        ) from exc
    return {"status": "connected"}


@router.get("/status")
async def telegram_status(
    user: User = Depends(authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | bool | None]:
    auth = await db.get(TelegramAuth, user.id)
    connected = bool(auth and auth.connected_at and auth.encrypted_session)
    return {
        "connected": connected,
        "password_required": bool(auth and auth.password_required),
        "pending": bool(auth and auth.pending_phone and auth.phone_code_hash),
        "connected_at": auth.connected_at.isoformat() if auth and auth.connected_at else None,
    }
