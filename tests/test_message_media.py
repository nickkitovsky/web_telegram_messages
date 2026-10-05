from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from saved_messages import media
from saved_messages.config import settings
from saved_messages.media import DownloadedMedia
from saved_messages.routes import messages as message_routes
from saved_messages.routes.messages import get_message_media


@pytest.mark.asyncio
async def test_download_media_stores_file_in_user_scoped_storage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "media_storage_path", str(tmp_path))
    monkeypatch.setattr(media, "is_downloadable_media", lambda message: True)
    monkeypatch.setattr(
        media,
        "_media_metadata",
        lambda message: ("image/jpeg", "image", "photo.jpg"),
    )

    class FakeClient:
        async def download_media(self, message: object, file: str) -> str:
            Path(file).write_bytes(b"image-data")
            return file

    message = SimpleNamespace(id=17, file=SimpleNamespace(ext=".jpg"))

    result = await media.download_message_media(FakeClient(), message, user_id=4)

    assert result is not None
    assert result.path == "4/17.jpg"
    assert result.mime_type == "image/jpeg"
    assert result.kind == "image"
    assert (tmp_path / "4" / "17.jpg").read_bytes() == b"image-data"


@pytest.mark.asyncio
async def test_media_download_failure_is_not_reported_as_a_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "media_storage_path", str(tmp_path))
    monkeypatch.setattr(media, "is_downloadable_media", lambda message: True)
    monkeypatch.setattr(
        media,
        "_media_metadata",
        lambda message: ("video/mp4", "video", "clip.mp4"),
    )

    class FakeClient:
        async def download_media(self, message: object, file: str) -> None:
            return None

    result = await media.download_message_media(
        FakeClient(),
        SimpleNamespace(id=21, file=SimpleNamespace(ext=".mp4")),
        user_id=4,
    )

    assert result is None


def test_telethon_photo_and_audio_video_documents_are_supported() -> None:
    from datetime import datetime

    from telethon.tl import types

    photo = types.MessageMediaPhoto(
        photo=types.Photo(
            id=1,
            access_hash=1,
            file_reference=b"",
            date=datetime.now(),
            sizes=[],
            dc_id=1,
        )
    )
    document = types.Document(
        id=2,
        access_hash=2,
        file_reference=b"",
        date=datetime.now(),
        mime_type="video/mp4",
        size=100,
        dc_id=1,
        attributes=[],
    )

    assert media.is_downloadable_media(SimpleNamespace(media=photo))
    assert media.is_downloadable_media(
        SimpleNamespace(media=types.MessageMediaDocument(document=document))
    )
    assert not media.is_downloadable_media(
        SimpleNamespace(media=types.MessageMediaWebPage(webpage=None))
    )


@pytest.mark.asyncio
async def test_media_endpoint_streams_only_the_authenticated_users_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "media_storage_path", str(tmp_path))
    media_file = tmp_path / "4" / "17.jpg"
    media_file.parent.mkdir(parents=True)
    media_file.write_bytes(b"image-data")
    message = SimpleNamespace(
        id=17,
        user_id=4,
        media_path="4/17.jpg",
        media_mime_type="image/jpeg",
        media_file_name="photo.jpg",
    )

    class FakeDB:
        async def scalar(self, statement: object) -> SimpleNamespace:
            return message

    response = await get_message_media(
        message_id=17,
        user=SimpleNamespace(id=4),
        db=FakeDB(),
    )

    assert Path(response.path) == media_file.resolve()
    assert response.media_type == "image/jpeg"
    assert response.headers["content-disposition"].startswith("inline;")


@pytest.mark.asyncio
async def test_media_endpoint_returns_not_found_for_another_users_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FakeDB:
        async def scalar(self, statement: object) -> None:
            return None

    with pytest.raises(HTTPException) as error:
        await get_message_media(
            message_id=17,
            user=SimpleNamespace(id=999),
            db=FakeDB(),
        )

    assert error.value.status_code == 404


@pytest.mark.asyncio
async def test_media_endpoint_downloads_and_caches_missing_local_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(settings, "media_storage_path", str(tmp_path))
    message = SimpleNamespace(
        id=17,
        user_id=4,
        telegram_message_id=900,
        media_path=None,
        media_mime_type="image/jpeg",
        media_file_name="photo.jpg",
        media_kind="image",
    )
    auth = SimpleNamespace(connected_at="connected")
    remote = SimpleNamespace(id=900)

    class FakeDB:
        async def scalar(self, statement: object) -> SimpleNamespace:
            return message

        async def get(self, model: object, user_id: int) -> SimpleNamespace:
            return auth

        async def commit(self) -> None:
            return None

    class FakeClient:
        async def get_messages(self, peer: str, ids: int) -> SimpleNamespace:
            assert peer == "me"
            assert ids == 900
            return remote

        async def disconnect(self) -> None:
            return None

    async def get_client(value: object) -> FakeClient:
        assert value is auth
        return FakeClient()

    async def download(client: object, value: object, user_id: int) -> DownloadedMedia:
        assert value is remote
        assert user_id == 4
        local_file = tmp_path / "4" / "900.jpg"
        local_file.parent.mkdir(parents=True)
        local_file.write_bytes(b"cached-image")
        return DownloadedMedia("4/900.jpg", "image/jpeg", "photo.jpg", "image")

    monkeypatch.setattr(message_routes, "get_client", get_client)
    monkeypatch.setattr(message_routes, "download_message_media", download)

    response = await get_message_media(message_id=17, user=SimpleNamespace(id=4), db=FakeDB())

    assert message.media_path == "4/900.jpg"
    assert Path(response.path).read_bytes() == b"cached-image"
