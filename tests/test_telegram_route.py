from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from saved_messages import telegram as telegram_client
from saved_messages.routes import telegram
from saved_messages.schemas import TelegramCode, TelegramPhone


@pytest.mark.asyncio
async def test_start_login_maps_connection_reset_to_actionable_service_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def get_auth(*args: object, **kwargs: object) -> object:
        return object()

    async def fail_to_connect(*args: object) -> None:
        raise ConnectionError("connection reset")

    monkeypatch.setattr(telegram, "get_telegram_auth", get_auth)
    monkeypatch.setattr(telegram, "start_login", fail_to_connect)

    with pytest.raises(HTTPException) as error:
        await telegram.begin_telegram_login(
            TelegramPhone(phone="+1234567890"),
            user=SimpleNamespace(id=1),
            db=object(),
        )

    assert error.value.status_code == 503
    assert "TELEGRAM_PROXY_URL" in error.value.detail


@pytest.mark.asyncio
async def test_code_response_explicitly_requests_telegram_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth = object()

    async def get_auth(*args: object, **kwargs: object) -> object:
        return auth

    async def needs_password(*args: object) -> bool:
        return False

    monkeypatch.setattr(telegram, "get_telegram_auth", get_auth)
    monkeypatch.setattr(telegram, "submit_code", needs_password)

    result = await telegram.telegram_code(
        TelegramCode(code="12345"),
        user=SimpleNamespace(id=1),
        db=object(),
    )

    assert result == {
        "status": "password_required",
        "authorized": False,
        "password_required": True,
    }


@pytest.mark.asyncio
async def test_telegram_status_reports_persisted_session() -> None:
    auth = SimpleNamespace(
        encrypted_session="encrypted-session",
        connected_at=datetime.now(UTC),
        password_required=False,
        pending_phone=None,
        phone_code_hash=None,
    )

    class FakeDB:
        async def get(self, model: object, user_id: int) -> SimpleNamespace:
            return auth

    result = await telegram.telegram_status(user=SimpleNamespace(id=7), db=FakeDB())

    assert result["connected"] is True
    assert result["password_required"] is False


@pytest.mark.asyncio
async def test_home_page_shows_telegram_session_indicator() -> None:
    from saved_messages.main import home

    html = (await home()).body.decode()

    assert 'id="telegram-indicator"' in html
    assert "loadTelegramStatus()" in html
    assert "result.password_required" in html
    assert "Telegram подключён" in html
    assert "сессия сохранена" in html
    assert "for(let attempt=0;attempt<30;attempt++)" in html
    assert "TaskIQ worker" in html
    assert "Медиа или сообщение без текста" in html
    assert "/tasks/media" in html
    assert "Загружаю вложение" in html
    assert "function renderText(value,entities=[])" in html
    assert 'target="_blank"' in html
    assert "https?:\\/\\/" in html
    assert "renderText(message.text,message.text_entities)" in html
    assert "--nord0:#2e3440" in html
    assert 'href="/static/favicon.png"' in html


@pytest.mark.asyncio
async def test_successful_telegram_login_persists_encrypted_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    auth = SimpleNamespace(
        encrypted_session=None,
        pending_phone="+1234567890",
        phone_code_hash="code-hash",
        password_required=True,
        connected_at=None,
    )

    class FakeDB:
        committed = False

        async def commit(self) -> None:
            self.committed = True

    class FakeClient:
        class Session:
            @staticmethod
            def save() -> str:
                return "telethon-session"

        session = Session()

    monkeypatch.setattr(
        telegram_client,
        "encrypt_telegram_session",
        lambda value: f"encrypted:{value}",
    )
    db = FakeDB()

    await telegram_client._complete_login(db, auth, FakeClient())

    assert auth.encrypted_session == "encrypted:telethon-session"
    assert auth.pending_phone is None
    assert auth.phone_code_hash is None
    assert auth.password_required is False
    assert auth.connected_at is not None
    assert db.committed
