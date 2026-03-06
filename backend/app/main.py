import json
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import parse_qs

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, model_validator

@asynccontextmanager
async def lifespan(_: FastAPI):
    _initialize_database()
    yield


app = FastAPI(title="Project Management MVP API", lifespan=lifespan)

FRONTEND_DIST_DIR = Path(__file__).resolve().parent.parent / "frontend_dist"
DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"

SESSION_COOKIE = "pm_session"
MVP_USERNAME = "user"
MVP_PASSWORD = "password"

INITIAL_BOARD = {
    "columns": [
        {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1", "card-2"]},
        {"id": "col-discovery", "title": "Discovery", "cardIds": ["card-3"]},
        {"id": "col-progress", "title": "In Progress", "cardIds": ["card-4", "card-5"]},
        {"id": "col-review", "title": "Review", "cardIds": ["card-6"]},
        {"id": "col-done", "title": "Done", "cardIds": ["card-7", "card-8"]},
    ],
    "cards": {
        "card-1": {
            "id": "card-1",
            "title": "Align roadmap themes",
            "details": "Draft quarterly themes with impact statements and metrics.",
        },
        "card-2": {
            "id": "card-2",
            "title": "Gather customer signals",
            "details": "Review support tags, sales notes, and churn feedback.",
        },
        "card-3": {
            "id": "card-3",
            "title": "Prototype analytics view",
            "details": "Sketch initial dashboard layout and key drill-downs.",
        },
        "card-4": {
            "id": "card-4",
            "title": "Refine status language",
            "details": "Standardize column labels and tone across the board.",
        },
        "card-5": {
            "id": "card-5",
            "title": "Design card layout",
            "details": "Add hierarchy and spacing for scanning dense lists.",
        },
        "card-6": {
            "id": "card-6",
            "title": "QA micro-interactions",
            "details": "Verify hover, focus, and loading states.",
        },
        "card-7": {
            "id": "card-7",
            "title": "Ship marketing page",
            "details": "Final copy approved and asset pack delivered.",
        },
        "card-8": {
            "id": "card-8",
            "title": "Close onboarding sprint",
            "details": "Document release notes and share internally.",
        },
    },
}


class CardPayload(BaseModel):
    id: str
    title: str
    details: str


class ColumnPayload(BaseModel):
    id: str
    title: str
    cardIds: list[str]


class BoardPayload(BaseModel):
    columns: list[ColumnPayload]
    cards: dict[str, CardPayload]

    @model_validator(mode="after")
    def validate_integrity(self) -> "BoardPayload":
        column_ids = [column.id for column in self.columns]
        if len(set(column_ids)) != len(column_ids):
            raise ValueError("Column IDs must be unique")

        card_ids = set(self.cards.keys())
        all_references: list[str] = []
        for card_id, card in self.cards.items():
            if card.id != card_id:
                raise ValueError(f"Card key {card_id} must match card.id")

        for column in self.columns:
            all_references.extend(column.cardIds)

        if len(set(all_references)) != len(all_references):
            raise ValueError("A card cannot exist in multiple columns")

        unknown_ids = [card_id for card_id in all_references if card_id not in card_ids]
        if unknown_ids:
            raise ValueError(f"Unknown card IDs in columns: {unknown_ids}")

        unreferenced = card_ids.difference(all_references)
        if unreferenced:
            raise ValueError(f"Unreferenced cards are not allowed: {sorted(unreferenced)}")

        return self


def _db_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with _db_connection() as connection:
        connection.executescript(
            """
            PRAGMA user_version = 1;

            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              password_plaintext TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
              updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            );

            CREATE TABLE IF NOT EXISTS boards (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL UNIQUE,
              title TEXT NOT NULL DEFAULT 'Kanban Board',
              board_json TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
              updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
              FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);
            """
        )

        connection.execute(
            """
            INSERT INTO users (username, password_plaintext)
            VALUES (?, ?)
            ON CONFLICT(username) DO NOTHING
            """,
            (MVP_USERNAME, MVP_PASSWORD),
        )

        user_id_row = connection.execute(
            "SELECT id FROM users WHERE username = ?",
            (MVP_USERNAME,),
        ).fetchone()

        if user_id_row is None:
            raise RuntimeError("Failed to initialize MVP user")

        connection.execute(
            """
            INSERT INTO boards (user_id, title, board_json)
            VALUES (?, 'Kanban Board', ?)
            ON CONFLICT(user_id) DO NOTHING
            """,
            (user_id_row["id"], json.dumps(INITIAL_BOARD)),
        )


def _get_user_by_username(username: str | None) -> sqlite3.Row | None:
    if not username:
        return None

    with _db_connection() as connection:
        return connection.execute(
            "SELECT id, username, password_plaintext FROM users WHERE username = ?",
            (username,),
        ).fetchone()


def _verify_credentials(username: str, password: str) -> bool:
    user = _get_user_by_username(username)
    return user is not None and user["password_plaintext"] == password


def _read_user_board(user_id: int) -> dict:
    with _db_connection() as connection:
        row = connection.execute(
            "SELECT board_json FROM boards WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return json.loads(row["board_json"])


def _write_user_board(user_id: int, board: dict) -> None:
    with _db_connection() as connection:
        result = connection.execute(
            """
            UPDATE boards
            SET board_json = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE user_id = ?
            """,
            (json.dumps(board), user_id),
        )

    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Board not found")


def _frontend_file(path: str) -> Path:
    normalized = path.lstrip("/")
    candidate = FRONTEND_DIST_DIR / normalized

    if candidate.is_dir():
        return candidate / "index.html"
    if candidate.exists():
        return candidate
    return FRONTEND_DIST_DIR / "index.html"


def _current_user(request: Request) -> sqlite3.Row | None:
    session_username = request.cookies.get(SESSION_COOKIE)
    return _get_user_by_username(session_username)


def _require_api_user(request: Request) -> sqlite3.Row:
    user = _current_user(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    return user


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


if (FRONTEND_DIST_DIR / "_next").exists():
    app.mount(
        "/_next",
        StaticFiles(directory=FRONTEND_DIST_DIR / "_next"),
        name="next-assets",
    )


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


@app.get("/api/board")
def get_board(request: Request) -> dict:
    user = _require_api_user(request)
    return {"board": _read_user_board(user["id"])}


@app.put("/api/board")
def put_board(request: Request, payload: BoardPayload) -> dict:
    user = _require_api_user(request)
    board = payload.model_dump()
    _write_user_board(user["id"], board)
    return {"board": board}


@app.get("/login", include_in_schema=False)
def login_page(request: Request, error: str | None = None) -> Response:
    if _current_user(request):
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return HTMLResponse(_login_html(show_error=error == "1"))


@app.post("/auth/login", include_in_schema=False)
async def login(request: Request) -> RedirectResponse:
    form_data = parse_qs((await request.body()).decode())
    username = form_data.get("username", [""])[0]
    password = form_data.get("password", [""])[0]

    if not _verify_credentials(username, password):
        return RedirectResponse(url="/login?error=1", status_code=status.HTTP_303_SEE_OTHER)

    response = RedirectResponse(url="/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=username,
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
    if _current_user(request) is None:
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

    if _current_user(request) is None:
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)

    file_path = _frontend_file(full_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Not found")

    return FileResponse(file_path)
