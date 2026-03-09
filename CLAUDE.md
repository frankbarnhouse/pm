# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AI-powered Kanban project management app. Next.js frontend + Python FastAPI backend, packaged in Docker. Users interact with a drag-and-drop board; an AI chat sidebar can create/edit/move/delete cards via OpenAI structured outputs.

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

**Frontend** (`frontend/`): Next.js 16, React 19, TypeScript strict mode, Tailwind CSS v4, @dnd-kit for drag-and-drop. Statically exported and served by the backend. Board state lives in React `useState`, loaded from `GET /api/board` on mount, persisted via `PUT /api/board`.

**Backend** (`backend/`): Single-file FastAPI app (`app/main.py`) handling auth, board CRUD, AI chat, and static file serving. SQLite database at `backend/data/app.db` stores board state as JSON blob. Session-based auth with HTTP-only cookies. AI integration in `app/ai_client.py`.

**AI Chat Flow**: User prompt + current board state + conversation history sent to OpenAI structured outputs API. Response includes assistant message and optional `board_update` with operations (`create_card`, `edit_card`, `move_card`, `delete_card`, `rename_column`). Operations are validated and applied atomically. Chat history is in-memory per session.

**API Routes**:
- `GET/PUT /api/board` - board state (auth required)
- `POST /api/chat` - AI chat with structured board operations (auth required)
- `POST /api/ai/connectivity` - OpenAI smoke test (auth required)
- `GET /api/health` - health check
- `POST /auth/login`, `POST /auth/logout` - session auth

**Board Data Model**: Columns have ordered `cardIds` arrays; cards stored in a flat `cards` dict keyed by ID. Pydantic validates referential integrity on every write.

## Key Conventions

- No emojis in code or documentation
- KISS: no over-engineering, no unnecessary defensive programming
- Diagnose root causes with evidence before fixing issues
- Frontend expects backend at same origin (`/api/*`, `/auth/*`)
- Preserve test IDs used by unit/e2e tests (`column-*`, `card-*`)
- Prefer pure helper functions for board operations to keep tests simple
- OpenAI model configurable via `OPENAI_MODEL` env var (default: `gpt-4.1-mini`)
- MVP auth: hardcoded credentials `user` / `password`
- Planning docs live in `docs/` (PLAN.md, DATA_MODEL.md)

## Color Scheme

- Accent Yellow: `#ecad0a`
- Blue Primary: `#209dd7`
- Purple Secondary: `#753991`
- Dark Navy: `#032147`
- Gray Text: `#888888`
