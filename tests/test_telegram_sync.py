from types import SimpleNamespace

import pytest

from saved_messages.tasks import fetch_saved_messages
from saved_messages.telegram import get_message_author, message_payload


class FakeTelegramClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, int]]] = []

    async def iter_messages(self, peer: str, **kwargs: int):
        self.calls.append((peer, kwargs))
        for message_id in range(5, 0, -1):
            yield SimpleNamespace(id=message_id)


@pytest.mark.asyncio
async def test_sync_fetches_at_most_50_latest_messages() -> None:
    client = FakeTelegramClient()

    messages = await fetch_saved_messages(client)

    assert len(messages) == 5
    assert client.calls == [("me", {"limit": 50})]


@pytest.mark.asyncio
async def test_sync_fetches_older_messages_before_telegram_id() -> None:
    client = FakeTelegramClient()

    await fetch_saved_messages(client, before_telegram_id=100)

    assert client.calls == [("me", {"limit": 50, "offset_id": 100})]


def test_saved_message_payload_preserves_telegram_album_id() -> None:
    message = SimpleNamespace(
        id=19,
        grouped_id=7001,
        message="Album caption",
        date=None,
    )

    payload = message_payload(message)

    assert payload["telegram_message_id"] == 19
    assert payload["telegram_grouped_id"] == 7001
    assert payload["is_forwarded"] is False


def test_saved_message_payload_serializes_telegram_formatting_entities() -> None:
    message = SimpleNamespace(
        id=20,
        grouped_id=None,
        message="😀 bold",
        date=None,
        entities=[
            type("MessageEntityBold", (), {"offset": 3, "length": 4})(),
            type(
                "MessageEntityTextUrl",
                (),
                {"offset": 0, "length": 2, "url": "https://example.com"},
            )(),
        ],
    )

    payload = message_payload(message)

    assert payload["text_entities"] == [
        {"type": "bold", "offset": 3, "length": 4},
        {"type": "text_url", "offset": 0, "length": 2, "url": "https://example.com"},
    ]


@pytest.mark.asyncio
async def test_forwarded_message_uses_source_channel_name() -> None:
    class FakeClient:
        async def get_entity(self, peer: object) -> SimpleNamespace:
            assert peer == "channel-peer"
            return SimpleNamespace(title="Interesting Channel")

    message = SimpleNamespace(
        fwd_from=SimpleNamespace(from_id="channel-peer", from_name=None),
        post_author=None,
    )

    assert (
        await get_message_author(FakeClient(), message, "My Telegram Name") == "Interesting Channel"
    )


@pytest.mark.asyncio
async def test_regular_saved_message_uses_telegram_account_name() -> None:
    class FakeClient:
        async def get_entity(self, peer: object) -> None:
            raise AssertionError("No source lookup is expected")

    message = SimpleNamespace(fwd_from=None)

    assert await get_message_author(FakeClient(), message, "My Telegram Name") == "My Telegram Name"
