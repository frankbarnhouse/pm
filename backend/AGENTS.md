# Backend Agent Notes

## Purpose

This folder contains the FastAPI backend for the Project Management MVP.

## Current scope (Part 2 scaffold)

- Temporary hello-world HTML page at `/` to validate single-container serving.
- Health endpoint at `/api/health` returning JSON.
- Python dependency management via `uv` using `pyproject.toml`.

## Files

- `backend/app/main.py`: FastAPI app with `/` and `/api/health` routes.
- `backend/pyproject.toml`: Python project metadata and dependencies.
- `backend/app/__init__.py`: Package marker for app module imports.

## Container behavior

- Container is built from repo-root `Dockerfile`.
- Runtime command: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- App listens on port `8000` inside container.

## Next expected changes

- Replace temporary root HTML with statically built frontend serving in Part 3.
- Add auth, persistence, and AI routes in later parts.