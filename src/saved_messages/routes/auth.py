from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from saved_messages.config import settings
from saved_messages.db import get_db
from saved_messages.dependencies import authenticated_user
from saved_messages.models import User
from saved_messages.schemas import Credentials, UserView
from saved_messages.security import (
    SESSION_COOKIE,
    SESSION_LIFETIME,
    create_session,
    hash_password,
    token_digest,
    verify_password,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserView, status_code=status.HTTP_201_CREATED)
async def register(
    payload: Credentials, response: Response, db: AsyncSession = Depends(get_db)
) -> User:
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password))
    db.add(user)
    try:
        await db.flush()
        token = await create_session(db, user)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="An account with this email already exists"
        ) from exc
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=int(SESSION_LIFETIME.total_seconds()),
    )
    return user


@router.post("/login", response_model=UserView)
async def login(
    payload: Credentials, response: Response, db: AsyncSession = Depends(get_db)
) -> User:
    user = await db.scalar(select(User).where(User.email == payload.email.lower()))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = await create_session(db, user)
    response.set_cookie(
        SESSION_COOKIE,
        token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="lax",
        max_age=int(SESSION_LIFETIME.total_seconds()),
    )
    return user


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    _: User = Depends(authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if token:
        from saved_messages.models import UserSession

        session = await db.scalar(
            select(UserSession).where(UserSession.token_hash == token_digest(token))
        )
        if session:
            await db.delete(session)
            await db.commit()
    response.delete_cookie(SESSION_COOKIE, httponly=True, samesite="lax")


@router.get("/me", response_model=UserView)
async def me(user: User = Depends(authenticated_user)) -> User:
    return user
