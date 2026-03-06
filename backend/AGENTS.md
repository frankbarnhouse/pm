# Backend Agent Notes

## Purpose

This folder contains the FastAPI backend for the Project Management MVP.

## Current scope (Part 4)

- FastAPI serves statically exported Next.js frontend at `/`.
- FastAPI serves Next.js static assets under `/_next/*`.
- Health endpoint at `/api/health` returning JSON.
- Login flow at `/login` with fixed credentials (`user` / `password`).
- Session cookie auth gates board routes; unauthenticated users are redirected to `/login`.
- Logout endpoint at `/auth/logout` clears the session cookie.
- Python dependency management via `uv` using `pyproject.toml`.

## Files

- `backend/app/main.py`: FastAPI app with health route, login/logout routes, and auth-gated frontend routing.
- `backend/pyproject.toml`: Python project metadata and dependencies.
- `backend/app/__init__.py`: Package marker for app module imports.
- `backend/tests/test_auth_flow.py`: backend auth/session integration tests.
- `backend/frontend_dist/` (container runtime path): exported Next.js frontend files.

## Container behavior

- Container is built from repo-root `Dockerfile`.
- Runtime command: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- App listens on port `8000` inside container.

## Next expected changes

- Add persistence and API data routes in later parts.
- Add AI routes in later parts.