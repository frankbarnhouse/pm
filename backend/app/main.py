from pathlib import Path
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

app = FastAPI(title="Project Management MVP API")

FRONTEND_DIST_DIR = Path(__file__).resolve().parent.parent / "frontend_dist"
SESSION_COOKIE = "pm_session"
SESSION_VALUE = "authenticated"
DEMO_USERNAME = "user"
DEMO_PASSWORD = "password"

if (FRONTEND_DIST_DIR / "_next").exists():
    app.mount(
        "/_next",
        StaticFiles(directory=FRONTEND_DIST_DIR / "_next"),
        name="next-assets",
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


def _frontend_file(path: str) -> Path:
    normalized = path.lstrip("/")
    candidate = FRONTEND_DIST_DIR / normalized

    if candidate.is_dir():
        return candidate / "index.html"
    if candidate.exists():
        return candidate
    return FRONTEND_DIST_DIR / "index.html"


def _is_authenticated(request: Request) -> bool:
    return request.cookies.get(SESSION_COOKIE) == SESSION_VALUE


def _login_html(show_error: bool) -> str:
    error_text = (
    "<p class=\"error\">Invalid credentials. Use user / password.</p>"
    if show_error
    else ""
    )
    return f"""<!doctype html>
<html lang=\"en\">
    <head>
        <meta charset=\"utf-8\" />
        <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
        <title>Sign In | Kanban Studio</title>
        <style>
            :root {{
                --accent-yellow: #ecad0a;
                --primary-blue: #209dd7;
                --secondary-purple: #753991;
                --navy-dark: #032147;
                --gray-text: #888888;
            }}
            body {{
                margin: 0;
                font-family: "Segoe UI", sans-serif;
                background: linear-gradient(165deg, #f9fbff 0%, #eef5ff 100%);
                color: var(--navy-dark);
            }}
            main {{
                max-width: 420px;
                margin: 88px auto;
                padding: 28px;
                border-radius: 16px;
                border: 1px solid rgba(3, 33, 71, 0.08);
                background: #fff;
                box-shadow: 0 18px 40px rgba(3, 33, 71, 0.12);
            }}
            h1 {{
                margin: 0 0 8px;
            }}
            p {{
                margin: 0 0 18px;
                color: var(--gray-text);
            }}
            label {{
                display: block;
                margin-bottom: 8px;
                font-size: 13px;
                font-weight: 700;
            }}
            input {{
                width: 100%;
                margin-bottom: 14px;
                padding: 10px 12px;
                border-radius: 10px;
                border: 1px solid rgba(3, 33, 71, 0.15);
                box-sizing: border-box;
            }}
            button {{
                width: 100%;
                border: 0;
                border-radius: 999px;
                padding: 10px 14px;
                color: #fff;
                background: var(--secondary-purple);
                font-weight: 700;
                cursor: pointer;
            }}
            .hint {{
                margin-top: 12px;
                font-size: 12px;
            }}
            .error {{
                margin-bottom: 12px;
                color: #a22;
                font-weight: 700;
            }}
        </style>
    </head>
    <body>
        <main>
            <h1>Sign in</h1>
            <p>Use the MVP credentials to access the board.</p>
            {error_text}
            <form method=\"post\" action=\"/auth/login\">
                <label for=\"username\">Username</label>
                <input id=\"username\" name=\"username\" required />
                <label for=\"password\">Password</label>
                <input id=\"password\" name=\"password\" type=\"password\" required />
                <button type=\"submit\">Sign in</button>
            </form>
            <p class=\"hint\">Username: <strong>user</strong>, Password: <strong>password</strong></p>
        </main>
    </body>
</html>
"""


@app.get("/login", include_in_schema=False)
def login_page(request: Request, error: str | None = None) -> Response:
    if _is_authenticated(request):
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return HTMLResponse(_login_html(show_error=error == "1"))


@app.post("/auth/login", include_in_schema=False)
async def login(request: Request) -> RedirectResponse:
    form_data = parse_qs((await request.body()).decode())
    username = form_data.get("username", [""])[0]
    password = form_data.get("password", [""])[0]

    if username != DEMO_USERNAME or password != DEMO_PASSWORD:
        return RedirectResponse(url="/login?error=1", status_code=status.HTTP_303_SEE_OTHER)

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=SESSION_VALUE,
        httponly=True,
        samesite="lax",
    )
    return response


@app.post("/auth/logout", include_in_schema=False)
def logout() -> RedirectResponse:
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(SESSION_COOKIE)
    return response


@app.get("/", include_in_schema=False)
def home(request: Request) -> Response:
    if not _is_authenticated(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    index_file = FRONTEND_DIST_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=500, detail="Frontend build not found")
    return FileResponse(index_file)


@app.get("/{full_path:path}", include_in_schema=False)
def frontend_routes(request: Request, full_path: str) -> Response:
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    if full_path.startswith("auth/") or full_path == "login":
        raise HTTPException(status_code=404, detail="Not found")

    if not _is_authenticated(request):
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    file_path = _frontend_file(full_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Not found")

    return FileResponse(file_path)
