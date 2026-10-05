from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from saved_messages.routes import tasks
from saved_messages.schemas import MessageMediaRequest


@pytest.mark.asyncio
async def test_media_hydration_task_is_scoped_and_queued(monkeypatch: pytest.MonkeyPatch) -> None:
    rows = [
        SimpleNamespace(id=10, telegram_message_id=101, media_checked=False),
        SimpleNamespace(id=11, telegram_message_id=102, media_checked=True),
    ]

    class FakeScalars:
        def all(self) -> list[SimpleNamespace]:
            return rows

    class FakeDB:
        async def scalars(self, statement: object) -> FakeScalars:
            return FakeScalars()

    class FakeTask:
        async def kiq(self, user_id: int, telegram_ids: list[int]) -> SimpleNamespace:
            assert user_id == 7
            assert telegram_ids == [101]
            return SimpleNamespace(task_id="media-task-id")

    monkeypatch.setattr(tasks, "hydrate_saved_message_media", FakeTask())

    result = await tasks.queue_media_hydration(
        MessageMediaRequest(message_ids=[10, 11, 10]),
        user=SimpleNamespace(id=7),
        db=FakeDB(),
    )

    assert result == {"task_id": "media-task-id", "status": "queued", "count": 1}


@pytest.mark.asyncio
async def test_media_hydration_rejects_messages_outside_the_signed_in_user() -> None:
    class FakeScalars:
        def all(self) -> list[SimpleNamespace]:
            return []

    class FakeDB:
        async def scalars(self, statement: object) -> FakeScalars:
            return FakeScalars()

    with pytest.raises(HTTPException) as error:
        await tasks.queue_media_hydration(
            MessageMediaRequest(message_ids=[10]),
            user=SimpleNamespace(id=7),
            db=FakeDB(),
        )

    assert error.value.status_code == 404
