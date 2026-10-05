from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from taskiq.exceptions import SendTaskError

from saved_messages.db import get_db
from saved_messages.dependencies import authenticated_user
from saved_messages.models import SavedMessage, User
from saved_messages.schemas import MessageMediaRequest
from saved_messages.tasks import hydrate_saved_message_media, sync_telegram_user

router = APIRouter(prefix="/tasks", tags=["background tasks"])


@router.post("/sync", status_code=status.HTTP_202_ACCEPTED)
async def queue_sync(
    before_telegram_id: int | None = Query(default=None, gt=0),
    user: User = Depends(authenticated_user),
) -> dict[str, str]:
    try:
        task = await sync_telegram_user.kiq(user.id, before_telegram_id)
    except (ConnectionError, SendTaskError) as exc:
        raise HTTPException(status_code=503, detail="Background queue is unavailable") from exc
    return {
        "task_id": task.task_id,
        "status": "queued",
        "batch": "older" if before_telegram_id is not None else "latest",
        "limit": "50",
    }


@router.post("/media", status_code=status.HTTP_202_ACCEPTED)
async def queue_media_hydration(
    payload: MessageMediaRequest,
    user: User = Depends(authenticated_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str | int]:
    message_ids = list(dict.fromkeys(payload.message_ids))
    messages = await db.scalars(
        select(SavedMessage).where(
            SavedMessage.id.in_(message_ids),
            SavedMessage.user_id == user.id,
        )
    )
    rows = messages.all()
    if len(rows) != len(message_ids):
        raise HTTPException(status_code=404, detail="One or more messages were not found")
    telegram_ids = [message.telegram_message_id for message in rows if not message.media_checked]
    if not telegram_ids:
        return {"status": "complete", "checked": 0}
    try:
        task = await hydrate_saved_message_media.kiq(user.id, telegram_ids)
    except (ConnectionError, SendTaskError) as exc:
        raise HTTPException(status_code=503, detail="Background queue is unavailable") from exc
    return {"task_id": task.task_id, "status": "queued", "count": len(telegram_ids)}
