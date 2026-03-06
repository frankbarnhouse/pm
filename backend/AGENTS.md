# Backend Agent Notes

## Purpose

This folder contains the FastAPI backend for the Project Management MVP.

## Current scope (Part 6)

- FastAPI serves statically exported Next.js frontend at `/`.
- FastAPI serves Next.js static assets under `/_next/*`.
- Health endpoint at `/api/health` returning JSON.
- Login flow at `/login` with fixed credentials (`user` / `password`).
- Session cookie auth gates board routes; unauthenticated users are redirected to `/login`.
- Logout endpoint at `/auth/logout` clears the session cookie.
- SQLite DB initialization on startup, creating DB/tables if missing.
- Board API endpoints:
- `GET /api/board` (read current user's board)
- `PUT /api/board` (overwrite current user's board with validated payload)
- Python dependency management via `uv` using `pyproject.toml`.

## Files

- `backend/app/main.py`: FastAPI app with health route, login/logout routes, and auth-gated frontend routing.
- `backend/pyproject.toml`: Python project metadata and dependencies.
- `backend/app/__init__.py`: Package marker for app module imports.
- `backend/tests/test_auth_flow.py`: backend auth/session integration tests.
- `backend/tests/test_board_api.py`: backend DB init and board API tests.
- `backend/frontend_dist/` (container runtime path): exported Next.js frontend files.
- `backend/data/app.db` (runtime): local SQLite DB, persisted via scripts bind mount.

## Container behavior

- Container is built from repo-root `Dockerfile`.
- Runtime command: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- App listens on port `8000` inside container.

## Next expected changes

- Connect frontend state to backend board API in Part 7.
- Add AI routes in later parts.