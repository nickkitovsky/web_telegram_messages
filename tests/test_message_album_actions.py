from types import SimpleNamespace

import pytest
from fastapi import Response

from saved_messages.routes import messages


@pytest.mark.asyncio
async def test_deleting_an_album_removes_every_telegram_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = SimpleNamespace(
        id=1,
        user_id=7,
        telegram_message_id=101,
        telegram_grouped_id=9001,
    )
    second = SimpleNamespace(
        id=2,
        user_id=7,
        telegram_message_id=102,
        telegram_grouped_id=9001,
    )
    deleted_rows: list[SimpleNamespace] = []
    telegram_deleted: list[int] = []

    class FakeScalars:
        def all(self) -> list[SimpleNamespace]:
            return [first, second]

    class FakeDB:
        async def scalar(self, statement: object) -> SimpleNamespace:
            return first

        async def scalars(self, statement: object) -> FakeScalars:
            return FakeScalars()

        async def get(self, model: object, user_id: int) -> SimpleNamespace:
            return SimpleNamespace(connected_at=True)

        async def delete(self, row: SimpleNamespace) -> None:
            deleted_rows.append(row)

        async def commit(self) -> None:
            return None

    class FakeClient:
        async def delete_messages(self, peer: str, ids: list[int]) -> None:
            assert peer == "me"
            telegram_deleted.extend(ids)

        async def disconnect(self) -> None:
            return None

    async def fake_get_client(auth: object) -> FakeClient:
        return FakeClient()

    monkeypatch.setattr(messages, "get_client", fake_get_client)

    response = await messages.delete_message(
        message_id=1,
        user=SimpleNamespace(id=7),
        db=FakeDB(),
    )

    assert isinstance(response, Response)
    assert telegram_deleted == [101, 102]
    assert deleted_rows == [first, second]
