# Scripts Agent Notes

## Purpose

This folder contains cross-platform scripts for running the MVP in Docker.

## Naming convention

- macOS: `start-mac.sh`, `stop-mac.sh`
- Linux: `start-linux.sh`, `stop-linux.sh`
- Windows PowerShell: `start-windows.ps1`, `stop-windows.ps1`

## Shared behavior

- Use one image name: `udemy-pm-mvp`
- Use one container name: `udemy-pm-mvp`
- App is exposed at `http://localhost:8000`
- Start scripts:
- build image
- remove existing container with same name if present
- ensure local `backend/data` exists
- run container detached with `.env` loaded
- bind-mount `backend/data` to `/app/backend/data` for DB persistence
- Stop scripts:
- remove the container if present
- print a no-op message when container does not exist

## Usage

- Run from repo root so Docker build context includes all required files.