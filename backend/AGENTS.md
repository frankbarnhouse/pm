# Backend Agent Notes

## Purpose

This folder contains the FastAPI backend for the Project Management MVP.

## Current scope (Part 3)

- FastAPI serves statically exported Next.js frontend at `/`.
- FastAPI serves Next.js static assets under `/_next/*`.
- Health endpoint at `/api/health` returning JSON.
- Python dependency management via `uv` using `pyproject.toml`.

## Files

- `backend/app/main.py`: FastAPI app with `/api/health` plus frontend static file routing.
- `backend/pyproject.toml`: Python project metadata and dependencies.
- `backend/app/__init__.py`: Package marker for app module imports.
- `backend/frontend_dist/` (container runtime path): exported Next.js frontend files.

## Container behavior

- Container is built from repo-root `Dockerfile`.
- Runtime command: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`.
- App listens on port `8000` inside container.

## Next expected changes

- Add sign-in/session flow in Part 4.
- Add persistence and AI routes in later parts.