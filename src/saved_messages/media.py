import mimetypes
import re
from dataclasses import dataclass
from pathlib import Path

from telethon import TelegramClient
from telethon.tl import types

from saved_messages.config import settings


@dataclass(frozen=True)
class DownloadedMedia:
    path: str
    mime_type: str
    file_name: str
    kind: str


def is_downloadable_media(message: object) -> bool:
    media = getattr(message, "media", None)
    return isinstance(media, (types.MessageMediaPhoto, types.MessageMediaDocument))


def _media_metadata(message: object) -> tuple[str, str, str]:
    file = message.file
    mime_type = file.mime_type or "application/octet-stream"
    attributes = getattr(file, "attributes", ())
    if isinstance(message.media, types.MessageMediaPhoto) or mime_type.startswith("image/"):
        kind = "image"
    elif any(isinstance(attr, types.DocumentAttributeVideo) for attr in attributes):
        kind = "video"
        if mime_type == "application/octet-stream":
            mime_type = "video/mp4"
    elif any(isinstance(attr, types.DocumentAttributeAudio) for attr in attributes):
        kind = "audio"
        if mime_type == "application/octet-stream":
            mime_type = (
                "audio/mpeg" if file.name and file.name.lower().endswith(".mp3") else "audio/ogg"
            )
    elif mime_type.startswith("video/"):
        kind = "video"
    elif mime_type.startswith("audio/"):
        kind = "audio"
    else:
        kind = "file"
    return mime_type, kind, file.name or ""


def media_metadata(message: object) -> tuple[str, str, str]:
    return _media_metadata(message)


async def download_message_media(
    client: TelegramClient, message: object, user_id: int
) -> DownloadedMedia | None:
    if not is_downloadable_media(message):
        return None

    mime_type, kind, original_name = _media_metadata(message)
    extension = Path(original_name).suffix
    if not re.fullmatch(r"\.[A-Za-z0-9]{1,12}", extension):
        extension = (
            getattr(message.file, "ext", None) or mimetypes.guess_extension(mime_type) or ".bin"
        )
    if not re.fullmatch(r"\.[A-Za-z0-9]{1,12}", extension):
        extension = ".bin"

    relative_path = Path(str(user_id)) / f"{message.id}{extension}"
    media_root = Path(settings.media_storage_path).resolve()
    target = (media_root / relative_path).resolve()
    if not target.is_relative_to(media_root):
        raise ValueError("Telegram media path resolved outside the configured storage directory")
    target.parent.mkdir(parents=True, exist_ok=True)

    downloaded = await client.download_media(message, file=str(target))
    if downloaded is None or not target.is_file():
        return None

    safe_name = Path(original_name).name if original_name else target.name
    return DownloadedMedia(
        path=relative_path.as_posix(),
        mime_type=mime_type,
        file_name=safe_name[:255],
        kind=kind,
    )
