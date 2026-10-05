from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import Response

from saved_messages.routes.messages import list_messages


class FakeScalars:
    def __init__(self, values: list[SimpleNamespace]) -> None:
        self.values = values

    def all(self) -> list[SimpleNamespace]:
        return self.values


class FakeDB:
    def __init__(
        self,
        messages: list[SimpleNamespace],
        auth: SimpleNamespace | None,
        page_keys: list[int],
    ) -> None:
        self.messages = messages
        self.auth = auth
        self.page_keys = page_keys

    async def scalars(self, statement: object) -> FakeScalars:
        return FakeScalars(self.messages)

    async def execute(self, statement: object) -> SimpleNamespace:
        return SimpleNamespace(
            all=lambda: [SimpleNamespace(group_key=key) for key in self.page_keys]
        )

    async def get(self, model: object, user_id: int) -> SimpleNamespace | None:
        return self.auth

    async def scalar(self, statement: object) -> int | None:
        ids = [item.telegram_message_id for item in self.messages]
        return min(ids) if ids else None


def message(message_id: int) -> SimpleNamespace:
    return SimpleNamespace(
        id=message_id,
        telegram_message_id=message_id,
        telegram_grouped_id=None,
        text="note",
        text_entities=[],
        title="note",
        message_date=datetime.now(UTC),
        channel=None,
        is_forwarded=False,
        tags=[],
        archived=False,
        classification_confidence=0.9,
        classification_candidates=[],
        media_path=None,
        media_mime_type=None,
        media_file_name=None,
        media_kind=None,
        media_checked=True,
    )


@pytest.mark.asyncio
async def test_messages_page_has_next_when_an_extra_local_message_exists() -> None:
    response = Response()
    db = FakeDB([message(1), message(2), message(3)], auth=None, page_keys=[-1, -2, -3])

    page = await list_messages(
        response,
        q=None,
        tag=None,
        include_archived=False,
        limit=2,
        offset=0,
        user=SimpleNamespace(id=1),
        db=db,
    )

    assert [item.id for item in page] == [1, 2]
    assert response.headers["X-Has-Next"] == "true"
    assert response.headers["X-Has-Previous"] == "false"
    assert response.headers["X-Older-Telegram-ID"] == "1"


@pytest.mark.asyncio
async def test_messages_page_exposes_older_telegram_batches() -> None:
    response = Response()
    db = FakeDB(
        [message(3), message(2)],
        auth=SimpleNamespace(sync_has_more=True),
        page_keys=[-3, -2],
    )

    page = await list_messages(
        response,
        q=None,
        tag=None,
        include_archived=False,
        limit=2,
        offset=2,
        user=SimpleNamespace(id=1),
        db=db,
    )

    assert [item.id for item in page] == [3, 2]
    assert response.headers["X-Has-Next"] == "true"
    assert response.headers["X-Has-Previous"] == "true"


@pytest.mark.asyncio
async def test_archive_does_not_report_unfetched_telegram_batches() -> None:
    response = Response()
    db = FakeDB([], auth=SimpleNamespace(sync_has_more=True), page_keys=[])

    page = await list_messages(
        response,
        q=None,
        tag=None,
        include_archived=False,
        archived_only=True,
        limit=50,
        offset=0,
        user=SimpleNamespace(id=1),
        db=db,
    )

    assert page == []
    assert response.headers["X-Has-Next"] == "false"


@pytest.mark.asyncio
async def test_album_messages_are_returned_as_one_feed_item() -> None:
    response = Response()
    first = message(1)
    first.telegram_message_id = 101
    first.telegram_grouped_id = 7001
    first.message_date = datetime(2026, 10, 5, 12, 1, tzinfo=UTC)
    first.text = "Album caption"
    first.text_entities = [{"type": "bold", "offset": 6, "length": 7}]
    first.media_mime_type = "image/jpeg"
    first.media_file_name = "first.jpg"
    first.media_kind = "image"
    first.media_path = "7/101.jpg"
    second = message(2)
    second.telegram_message_id = 102
    second.telegram_grouped_id = 7001
    second.message_date = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)
    second.text = "😀 second"
    second.text_entities = [{"type": "italic", "offset": 3, "length": 6}]
    second.media_mime_type = "video/mp4"
    second.media_file_name = "second.mp4"
    second.media_kind = "video"
    second.media_path = "7/102.mp4"
    db = FakeDB([first, second], auth=None, page_keys=[7001])

    page = await list_messages(
        response,
        q=None,
        tag=None,
        include_archived=False,
        limit=50,
        offset=0,
        user=SimpleNamespace(id=7),
        db=db,
    )

    assert len(page) == 1
    assert page[0].telegram_message_ids == [101, 102]
    assert page[0].message_ids == [1, 2]
    assert page[0].text == "Album caption\n😀 second"
    assert [entity.model_dump() for entity in page[0].text_entities] == [
        {"type": "bold", "offset": 6, "length": 7, "url": None, "language": None},
        {"type": "italic", "offset": 17, "length": 6, "url": None, "language": None},
    ]
    assert [file.media_kind for file in page[0].media_files] == ["image", "video"]
    assert page[0].archived is False
