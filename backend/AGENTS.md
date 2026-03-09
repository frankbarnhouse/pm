# Backend Agent Notes

## Purpose

This folder contains the FastAPI backend for the Project Management MVP.

## Current scope

- FastAPI serves statically exported Next.js frontend at `/`.
- FastAPI serves Next.js static assets under `/_next/*`.
- Health endpoint at `/api/health` returning JSON.
- Login flow at `/login` with fixed credentials (`user` / `password`).
- Server-side session tokens with HTTP-only cookies gate board routes.
- Logout endpoint at `/auth/logout` clears the session cookie.
- SQLite DB initialization on startup, creating DB/tables if missing.
- Passwords hashed with PBKDF2-HMAC-SHA256 + per-user salt.
- Board API endpoints:
  - `GET /api/board` (read current user's board)
  - `PUT /api/board` (overwrite current user's board with validated payload)
- AI chat endpoint:
  - `POST /api/chat` (structured chat with optional board operations)
- OpenAI connectivity endpoint:
  - `POST /api/ai/connectivity` (authenticated `2+2` smoke call)
- OpenAI model configurable via `OPENAI_MODEL` env var (default `gpt-4.1-mini`).
- Python dependency management via `uv` using `pyproject.toml`.

## Module structure

- `app/main.py`: App creation, lifespan, static file mount, router wiring.
- `app/models.py`: Pydantic models (board, card, column, operation payloads).
- `app/database.py`: DB_PATH, connection, schema init/migration, CRUD, credential verification.
- `app/board_ops.py`: Board operation logic (apply operations atomically with validation).
- `app/session.py`: Session store, chat history, auth helpers (current_user, require_api_user).
- `app/login_page.py`: Login HTML template generator.
- `app/ai_client.py`: OpenAI integration (connectivity check, structured chat).
- `app/routes/api.py`: API endpoints (health, board, AI connectivity, chat).
- `app/routes/auth.py`: Login/logout page routes.
- `app/routes/frontend.py`: Frontend static file serving, FRONTEND_DIST_DIR.

## Test files

- `tests/conftest.py`: Shared test helpers (make_test_client, login_test_client).
- `tests/test_auth_flow.py`: Auth/session integration tests.
- `tests/test_board_api.py`: DB init, migration, and board API tests.
- `tests/test_chat_api.py`: Chat endpoint tests (monkeypatches `app.routes.api`).
- `tests/test_ai_connectivity_api.py`: Connectivity endpoint tests.
- `tests/test_ai_client.py`: Unit tests for OpenAI wrapper.

## Runtime paths

- `backend/frontend_dist/` (container): exported Next.js frontend files.
- `backend/data/app.db` (runtime): local SQLite DB, persisted via scripts bind mount.

## Container behavior

- Container is built from repo-root `Dockerfile`.
- Runtime command: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- App listens on port `8000` inside container.
