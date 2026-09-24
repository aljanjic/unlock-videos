# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django REST backend for UnlockVideos: users upload audio/video, get a transcript, an AI summary, and chat with an OpenAI model grounded in the transcript. The React frontend is a separate repo (`aljanjic/unlock-videos-frontend`, dev origin `http://localhost:3000` is in `CORS_ALLOWED_ORIGINS`).

## Commands

```bash
cp .env.example .env              # fill SECRET_KEY, SECRET_JWT, DEBUG, OPENAI_API_KEY, OPENAI_MODEL (optional), KEY
pip install -r requirements.txt   # also needs ffmpeg on the system
python manage.py migrate
python manage.py runserver 8002

docker-compose up --build         # gunicorn on :8002, --timeout 300, repo bind-mounted at /app

python manage.py makemigrations unlock_videos
python unlock_videos/playground/generator.py   # prints a random value usable for SECRET_KEY / SECRET_JWT
```

There is no test suite, linter, or CI config. `python manage.py test` finds no tests.

## Architecture

- **Single package**: `unlock_videos/` is both the Django project (settings, urls, wsgi) and the only installed app (models, views, migrations). No separate app directory.
- **Function-based DRF views** in `views.py` (`@api_view` + `@permission_classes`), all routes declared directly in `unlock_videos/urls.py`. Auth is SimpleJWT (`/api/token/`, `/api/token/refresh/`; 5-min access, 1-day rotating refresh with blacklist).
- **One model**, `MediaFile` (FK `user`, related_name `media_owner`). `save()` derives `file_type` from the extension and raises `ValueError` for anything outside mp4/avi/mov/mp3/wav/aac. It saves twice and stores `size` in MB (rounded float in an `IntegerField`). Length calculation is commented out.
- **Transcription is local, not the Whisper API**: `whisper_utils.py` loads the `openai-whisper` `base` model at import time, so importing `views.py` loads the model (slow startup, memory heavy). Video is converted to `media/audio_<id>.wav` via moviepy first. Transcription runs synchronously in the request, which is why gunicorn needs the 300s timeout.
- **OpenAI usage** goes through the Responses API. The `openai` client is created at module level in `views.py` and reads `OPENAI_API_KEY` from env. The model comes from `settings.OPENAI_MODEL` (env `OPENAI_MODEL`, default `gpt-4o-mini`). The Assistants API (`client.beta.threads`/`assistants`) was shut down by OpenAI in Aug 2026 and now returns 404; don't use it.
  - `summary`: `utils.create_summary_from_transcript`, a single `responses.create` call that asks "What is this video about?".
  - `start` / `chat`: `start` creates an OpenAI conversation and returns its id as `thread_id` (field name kept for the frontend). `chat` calls `responses.create(conversation=thread_id, ...)`, so the conversation holds the history. Instructions aren't stored in the conversation, so the transcript is sent in `instructions` on every turn. Both share the `utils.TRANSCRIPT_INSTRUCTIONS` prompt.
- **Transcript handoff to chat goes through the Django cache**: `GET /api/files/<id>/` writes the transcript to the cache under the key from the `KEY` env var, and `/api/chat/` reads it back. The key is **global, not per user/file**, the cache is the default per-process LocMemCache, and `start`/`chat` have `IsAuthenticated` commented out. So the chat context is whichever file was opened last in that worker process. The commented-out code shows the intended per-user key `transcript_{user.id}_{file_id}`.

## Gotchas

- Env is read through `python-decouple`. A missing `SECRET_KEY` or `SECRET_JWT` fails when `settings.py` loads. `KEY` is only read at request time.
- `DEBUG=False` turns on `SECURE_SSL_REDIRECT`, so local HTTP requests get redirected to HTTPS. Use `DEBUG=True` for local dev.
- `MEDIA_URL` is never set, but `urls.py` calls `static(settings.MEDIA_URL, ...)` when `DEBUG` is on. Django rejects an empty prefix, so set `MEDIA_URL` if URL loading fails in debug mode.
- `ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS` are hardcoded in `settings.py` and include the production hosts (`api.aljanjic.com`).
- SQLite DB (`db.sqlite3`) and uploads (`media/`) live in the repo root.
- Some code comments are in Serbian.
