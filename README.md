# Telegram Saved Messages Organizer

FastAPI application for organizing your Telegram Saved Messages with a local LLM. It stores
Telegram messages and user-defined tags in PostgreSQL, runs background work through TaskIQ/Redis,
and keeps Telegram and LLM integration credentials on your machine.

## Local model recommendation

Start with **[Qwen3-0.6B GGUF, `Q4_K_M`](https://huggingface.co/unsloth/Qwen3-0.6B-GGUF/blob/main/Qwen3-0.6B-Q4_K_M.gguf)** (about 397 MB). It is a practical CPU-only option for a low-memory VPS and handles Russian and English. Smaller models can produce inconsistent tags, so review low-confidence predictions. If your machine has more memory, try Qwen3-1.7B `Q4_K_M` for better classification quality. Download the linked file and place it at `models/Qwen3-0.6B-Q4_K_M.gguf`, or set `LLM_MODEL_PATH`.

`llama-cpp-python` is an optional extra because compiling its native extension on Windows may
require a C++ build toolchain. Install it separately with `uv sync --extra llm` on a supported
machine. The rest of the application, including the database and Telegram integration, does not
require model weights.

## Setup

Python 3.14 is managed by uv. Install uv if needed, then run:

```powershell
uv python install 3.14
uv sync
Copy-Item .env.example .env
```

Set a random `APP_SECRET_KEY` and configure Telegram's `TELEGRAM_API_ID` and
`TELEGRAM_API_HASH` from <https://my.telegram.org>. Generate `TELEGRAM_SESSION_ENCRYPTION_KEY`
with:

```powershell
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Set `COOKIE_SECURE=true` when serving the application over HTTPS; keep it `false` for local HTTP.

### Telegram connection resets

If `POST /telegram/start` fails during `auth_key gen` with `ConnectionResetError` or
`WinError 10054`, this is a failure to establish Telethon's outbound MTProto connection to
Telegram, not an application login/session problem. A successful TCP probe to Telegram port 443
does not guarantee that the network permits MTProto. Try a different network or configure a
reachable SOCKS5/ SOCKS4/HTTP proxy in `.env`, then restart the app:

```dotenv
TELEGRAM_PROXY_URL=socks5://127.0.0.1:1080
```

Use the actual address and port of a trusted proxy that can reach Telegram. Credentials are
supported in the URL; keep `.env` private. The application uses the same proxy for the Telegram
login, sync and delete operations.

Start PostgreSQL and Redis and create the schema:

```powershell
docker compose up -d
uv run alembic upgrade head
```

Run the web application:

```powershell
uv run uvicorn saved_messages.main:app --reload
```

Open <http://127.0.0.1:8000/docs> to register/login and use the API. Registering the first account
does not require an external identity provider; passwords are Argon2-hashed and browser sessions
are opaque, random tokens stored as hashes.

## Background worker and scheduler

Start the worker and scheduler in separate terminals:

```powershell
uv run taskiq worker saved_messages.tasks:broker saved_messages.tasks
uv run taskiq scheduler saved_messages.tasks:scheduler
```

The web app's **Sync latest 50** button enqueues work; it does not run Telethon inside the Uvicorn
process. Keep the TaskIQ worker running or queued sync tasks will not write any messages to the
database. The page waits up to 30 seconds for the first messages and then reports the worker command
if the queue has not been processed.

Telegram media albums are identified by Telethon's `grouped_id` and displayed as one feed card
with all their attachments. Archiving, editing tags/title, and deleting a card apply to every
Telegram message in that album. Existing saved rows are backfilled with Telegram's album IDs the
next time their batch is synchronized.

The scheduler enqueues a sync every 15 minutes for Telegram-connected users. Each sync fetches at
most the 50 newest Saved Messages. The feed shows 50 messages per page; moving beyond locally
stored results enqueues the next 50 older Telegram messages using the oldest message ID as a
cursor. New messages are classified after synchronization. The account and Telegram APIs are
scoped to the authenticated user; Telegram sessions are encrypted using Fernet before they are
stored.

## API outline

- `POST /auth/register`, `POST /auth/login`, `POST /auth/logout`
- `POST /telegram/start`, `/telegram/code`, `/telegram/password`; `GET /telegram/status`
- `GET /messages?q=...&tag=...`, `PATCH /messages/{id}`, `DELETE /messages/{id}`
- `GET /tags`
- `POST /tasks/sync` queues a sync for the signed-in user

Message IDs in API paths are internal database IDs. Deleting a message also removes it from
Telegram Saved Messages; archiving only hides it from the default feed.

## Data model

`users` owns application accounts; `user_sessions` holds hashed browser session tokens;
`telegram_auth` stores encrypted Telethon sessions and in-progress login details;
`saved_messages` stores Telegram identifiers, text, title, date, channel and archive/classification
state and local media metadata; files are stored under `data/media/<user_id>/` and served only
through the authenticated `/messages/{id}/media` endpoint; `tags` plus `saved_message_tags` model
the many-to-many message/tag relationship. The
`(user_id, telegram_message_id)` unique constraint makes sync idempotent and protects user data
from crossing account boundaries.

Telegram Saved Messages do not expose stable public URLs for private attachments. Images, videos,
audio and documents are downloaded to the local `MEDIA_STORAGE_PATH` during sync and streamed
inline through the authenticated media endpoint. If a local copy is missing, the endpoint fetches
that attachment from Telegram and caches it locally. Pages containing older messages imported
before media support enqueue a background metadata/download check for those page records. The media
directory is excluded from version control; back it up separately if needed.

The Telegram login flow prompts for a two-step verification password when Telegram requests one.
After successful login, the encrypted Telethon session is stored per application user and reused
for future Telegram operations. The web interface shows whether that Telegram session is saved.

## Development

```powershell
uv run ruff check .
uv run pytest
```
