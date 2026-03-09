import sqlite3

from fastapi import HTTPException, Request

from app.database import get_user_by_username

SESSION_COOKIE = "pm_session"
MAX_CHAT_HISTORY_MESSAGES = 40

SESSION_STORE: dict[str, str] = {}
SESSION_CHAT_HISTORY: dict[str, list[dict[str, str]]] = {}


def get_session_history(request: Request) -> list[dict[str, str]]:
    session_token = request.cookies.get(SESSION_COOKIE)
    if not session_token or session_token not in SESSION_STORE:
        return []
    return SESSION_CHAT_HISTORY.setdefault(session_token, [])


def current_user(request: Request) -> sqlite3.Row | None:
    session_token = request.cookies.get(SESSION_COOKIE)
    if not session_token:
        return None
    username = SESSION_STORE.get(session_token)
    return get_user_by_username(username)


def require_api_user(request: Request) -> sqlite3.Row:
    user = current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user
