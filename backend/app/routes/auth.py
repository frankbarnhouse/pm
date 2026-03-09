from urllib.parse import parse_qs
from uuid import uuid4

from fastapi import APIRouter, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse, Response

from app.database import verify_credentials
from app.login_page import login_html
from app.session import (
    SESSION_CHAT_HISTORY,
    SESSION_COOKIE,
    SESSION_STORE,
    current_user,
)

router = APIRouter()


@router.get("/login", include_in_schema=False)
def login_page(request: Request, error: str | None = None) -> Response:
    if current_user(request):
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return HTMLResponse(login_html(show_error=error == "1"))


@router.post("/auth/login", include_in_schema=False)
async def login(request: Request) -> RedirectResponse:
    form_data = parse_qs((await request.body()).decode())
    username = form_data.get("username", [""])[0]
    password = form_data.get("password", [""])[0]

    if not verify_credentials(username, password):
        return RedirectResponse(url="/login?error=1", status_code=status.HTTP_303_SEE_OTHER)

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
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


@router.post("/auth/logout", include_in_schema=False)
def logout(request: Request) -> RedirectResponse:
    session_token = request.cookies.get(SESSION_COOKIE)
    if session_token:
        SESSION_STORE.pop(session_token, None)
        SESSION_CHAT_HISTORY.pop(session_token, None)

    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(SESSION_COOKIE)
    return response
