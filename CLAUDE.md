# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered Kanban project management app with multi-user and multi-board support. Next.js frontend + Python FastAPI backend, packaged in Docker. Users manage multiple Kanban boards with drag-and-drop; an AI chat sidebar can create/edit/move/delete cards via OpenAI structured outputs. Cards support priority levels and due dates.

## Commands

### Frontend (run from `frontend/`)
- `npm run dev` - dev server
- `npm run build` - production build (static export to `out/`)
- `npm run lint` - ESLint
- `npm run test:unit` - Vitest unit tests
- `npm run test:e2e` - Playwright end-to-end tests
- `npm run test:all` - both unit + e2e

### Backend (run from `backend/`)
- `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000` - run server
- `uv run pytest` - all backend tests
- `uv run pytest tests/test_board_api.py` - single test file
- `uv run pytest tests/test_board_api.py::test_name -v` - single test

### Docker (run from repo root)
- `docker build -t udemy_pm .` - build container
- Platform start/stop scripts in `scripts/`

## Architecture

**Frontend** (`frontend/`): Next.js 16, React 19, TypeScript strict mode, Tailwind CSS v4, @dnd-kit for drag-and-drop. Statically exported and served by the backend. SPA with two views:
- `BoardDashboard` - lists user's boards, create/edit/delete boards
- `KanbanBoard` - full board view with columns, cards, drag-and-drop, AI chat

Board state lives in React `useState`, loaded from `GET /api/boards/{id}` on mount, persisted via `PUT /api/boards/{id}`.

**Backend** (`backend/app/`): Modular FastAPI app. `main.py` is the thin entry point (app creation, lifespan, router wiring). Domain logic is split into:
- `models.py` - Pydantic models (board, card, column, operation payloads, registration, board CRUD)
- `database.py` - SQLite connection, schema init/migration, user CRUD, multi-board CRUD, credential verification
- `board_ops.py` - Board operation logic (apply operations atomically)
- `session.py` - In-memory session store, chat history, auth helpers (current_user, require_api_user)
- `login_page.py` - Login and registration HTML templates
- `ai_client.py` - OpenAI integration (connectivity check, structured chat)
- `routes/api.py` - API endpoints (health, boards CRUD, AI connectivity, chat)
- `routes/auth.py` - Login/logout/registration page routes
- `routes/frontend.py` - Static frontend serving, FRONTEND_DIST_DIR

SQLite database at `backend/data/app.db` stores board state as JSON blob. Session-based auth with HTTP-only cookies (server-side token store). Users can self-register.

**AI Chat Flow**: User prompt + current board state + conversation history sent to OpenAI structured outputs API. Response includes assistant message and optional `board_update` with operations (`create_card`, `edit_card`, `move_card`, `delete_card`, `rename_column`). Operations are validated and applied atomically. Chat history is in-memory per session.

**API Routes**:
- `GET /api/boards` - list user's boards (auth required)
- `POST /api/boards` - create board (auth required)
- `GET/PUT /api/boards/{id}` - board data (auth required)
- `PATCH /api/boards/{id}` - update board title/description (auth required)
- `DELETE /api/boards/{id}` - delete board (auth required)
- `POST /api/boards/{id}/chat` - AI chat for specific board (auth required)
- `GET/PUT /api/board` - legacy single-board endpoints (auth required)
- `POST /api/chat` - legacy AI chat (auth required)
- `POST /api/ai/connectivity` - OpenAI smoke test (auth required)
- `GET /api/health` - health check
- `POST /auth/login`, `POST /auth/register`, `POST /auth/logout` - session auth

**Board Data Model**: Columns have ordered `cardIds` arrays; cards stored in a flat `cards` dict keyed by ID. Cards optionally have `priority` (low/medium/high) and `due_date`. Pydantic validates referential integrity on every write. Each user can have multiple boards.

## Key Conventions

- No emojis in code or documentation
- KISS: no over-engineering, no unnecessary defensive programming
- Diagnose root causes with evidence before fixing issues
- Frontend expects backend at same origin (`/api/*`, `/auth/*`)
- Preserve test IDs used by unit/e2e tests (`column-*`, `card-*`, `board-card-*`, `open-board-*`)
- Prefer pure helper functions for board operations to keep tests simple
- OpenAI model configurable via `OPENAI_MODEL` env var (default: `gpt-4.1-mini`)
- Default MVP user: `user` / `password` (new users can self-register)
- Planning docs live in `docs/` (PLAN.md, DATA_MODEL.md)
- Boards are isolated per user (user A cannot access user B's boards)

## Color Scheme

- Accent Yellow: `#ecad0a`
- Blue Primary: `#209dd7`
- Purple Secondary: `#753991`
- Dark Navy: `#032147`
- Gray Text: `#888888`
