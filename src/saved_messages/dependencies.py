from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from saved_messages.db import get_db
from saved_messages.models import User
from saved_messages.security import get_current_user


async def authenticated_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    return await get_current_user(request, db)
