import sqlite3
from urllib.parse import parse_qs
from uuid import uuid4

from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.database import create_user, username_exists, verify_credentials
from app.login_page import login_html, register_html
from app.session import (
    SESSION_CHAT_HISTORY,
    SESSION_COOKIE,
    SESSION_STORE,
    current_user,
)

router = APIRouter()


def _create_session(username: str, redirect_url: str = "/") -> RedirectResponse:
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    session_token = uuid4().hex
    SESSION_STORE[session_token] = username
    SESSION_CHAT_HISTORY.setdefault(session_token, [])
    response.set_cookie(
        key=SESSION_COOKIE,
        value=session_token,
        httponly=True,
        samesite="strict",
    )
    return response


@router.get("/login", include_in_schema=False)
def login_page(request: Request, error: str | None = None) -> Response:
    if current_user(request):
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return HTMLResponse(login_html(show_error=error == "1"))


@router.get("/register", include_in_schema=False)
def register_page(request: Request, error: str | None = None) -> Response:
    if current_user(request):
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    error_messages = {
        "1": "Username is already taken.",
        "2": "Username must be 3-30 characters (letters, numbers, hyphens, underscores).",
        "3": "Password must be at least 4 characters.",
        "4": "Registration failed. Please try again.",
    }
    error_msg = error_messages.get(error or "", "")
    return HTMLResponse(register_html(error_message=error_msg))


@router.post("/auth/login", include_in_schema=False)
async def login(request: Request) -> RedirectResponse:
    form_data = parse_qs((await request.body()).decode())
    username = form_data.get("username", [""])[0]
    password = form_data.get("password", [""])[0]

    if not verify_credentials(username, password):
        return RedirectResponse(url="/login?error=1", status_code=status.HTTP_303_SEE_OTHER)

    return _create_session(username)


@router.post("/auth/register", include_in_schema=False)
async def register(request: Request) -> RedirectResponse:
    form_data = parse_qs((await request.body()).decode())
    username = form_data.get("username", [""])[0].strip()
    password = form_data.get("password", [""])[0]
    display_name = form_data.get("display_name", [""])[0].strip()

    if len(username) < 3 or len(username) > 30:
        return RedirectResponse(url="/register?error=2", status_code=status.HTTP_303_SEE_OTHER)

    if not username.replace("_", "").replace("-", "").isalnum():
        return RedirectResponse(url="/register?error=2", status_code=status.HTTP_303_SEE_OTHER)

    if len(password) < 4:
        return RedirectResponse(url="/register?error=3", status_code=status.HTTP_303_SEE_OTHER)

    if username_exists(username):
        return RedirectResponse(url="/register?error=1", status_code=status.HTTP_303_SEE_OTHER)

    try:
        create_user(username, password, display_name or username)
    except sqlite3.IntegrityError:
        return RedirectResponse(url="/register?error=1", status_code=status.HTTP_303_SEE_OTHER)
    except Exception:
        return RedirectResponse(url="/register?error=4", status_code=status.HTTP_303_SEE_OTHER)

    return _create_session(username)


@router.post("/auth/logout", include_in_schema=False)
def logout(request: Request) -> RedirectResponse:
    session_token = request.cookies.get(SESSION_COOKIE)
    if session_token:
        SESSION_STORE.pop(session_token, None)
        SESSION_CHAT_HISTORY.pop(session_token, None)

    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(SESSION_COOKIE)
    return response
