import hashlib
import json
import logging
import secrets
import sqlite3
from copy import deepcopy
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Literal
from urllib.parse import parse_qs
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, model_validator

from app.ai_client import (
    get_openai_model,
    OpenAIChatError,
    MissingApiKeyError,
    OpenAIConnectivityError,
    run_connectivity_check,
    run_structured_chat,
)

# Load environment variables from .env file (for local development)
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

logger = logging.getLogger(__name__)

MAX_CHAT_HISTORY_MESSAGES = 40


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

SESSION_STORE: dict[str, str] = {}
SESSION_CHAT_HISTORY: dict[str, list[dict[str, str]]] = {}

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


class ChatMessagePayload(BaseModel):
    prompt: str

    @model_validator(mode="after")
    def validate_prompt(self) -> "ChatMessagePayload":
        if not self.prompt.strip():
            raise ValueError("Prompt cannot be empty")
        return self


class CreateCardOperation(BaseModel):
    type: Literal["create_card"]
    column_id: str
    title: str
    details: str


class EditCardOperation(BaseModel):
    type: Literal["edit_card"]
    card_id: str
    title: str | None = None
    details: str | None = None

    @model_validator(mode="after")
    def validate_has_changes(self) -> "EditCardOperation":
        if self.title is None and self.details is None:
            raise ValueError("edit_card requires title and/or details")
        return self


class MoveCardOperation(BaseModel):
    type: Literal["move_card"]
    card_id: str
    to_column_id: str
    before_card_id: str | None = None


class DeleteCardOperation(BaseModel):
    type: Literal["delete_card"]
    card_id: str


class RenameColumnOperation(BaseModel):
    type: Literal["rename_column"]
    column_id: str
    title: str


BoardOperation = Annotated[
    CreateCardOperation
    | EditCardOperation
    | MoveCardOperation
    | DeleteCardOperation
    | RenameColumnOperation,
    Field(discriminator="type"),
]


class BoardUpdatePayload(BaseModel):
    operations: list[BoardOperation]


class AIChatResultPayload(BaseModel):
    assistant_message: str
    board_update: BoardUpdatePayload | None = None


def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 100000
    ).hex()


def _db_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {row["name"] for row in rows}


def _migrate_users_table(connection: sqlite3.Connection) -> set[str]:
    user_columns = _table_columns(connection, "users")

    if "password_hash" not in user_columns:
        connection.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        user_columns.add("password_hash")

    if "password_salt" not in user_columns:
        connection.execute("ALTER TABLE users ADD COLUMN password_salt TEXT")
        user_columns.add("password_salt")

    if "password_plaintext" in user_columns:
        legacy_users = connection.execute(
            """
            SELECT id, password_plaintext
            FROM users
            WHERE password_hash IS NULL OR password_salt IS NULL
            """
        ).fetchall()

        for row in legacy_users:
            salt = secrets.token_hex(16)
            hashed = _hash_password(row["password_plaintext"], salt)
            connection.execute(
                """
                UPDATE users
                SET password_hash = ?, password_salt = ?,
                    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
                WHERE id = ?
                """,
                (hashed, salt, row["id"]),
            )

    return user_columns


def _initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with _db_connection() as connection:
        connection.executescript(
            """
            PRAGMA user_version = 2;

            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              password_hash TEXT NOT NULL,
              password_salt TEXT NOT NULL,
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

        user_columns = _migrate_users_table(connection)

        salt = secrets.token_hex(16)
        hashed = _hash_password(MVP_PASSWORD, salt)

        if "password_plaintext" in user_columns:
            connection.execute(
                """
                INSERT INTO users (username, password_plaintext, password_hash, password_salt)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(username) DO NOTHING
                """,
                (MVP_USERNAME, MVP_PASSWORD, hashed, salt),
            )
        else:
            connection.execute(
                """
                INSERT INTO users (username, password_hash, password_salt)
                VALUES (?, ?, ?)
                ON CONFLICT(username) DO NOTHING
                """,
                (MVP_USERNAME, hashed, salt),
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
            "SELECT id, username, password_hash, password_salt FROM users WHERE username = ?",
            (username,),
        ).fetchone()


def _verify_credentials(username: str, password: str) -> bool:
    user = _get_user_by_username(username)
    if user is None:
        return False
    expected_hash = _hash_password(password, user["password_salt"])
    return user["password_hash"] == expected_hash


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


def _next_card_id(board: dict) -> str:
    max_suffix = 0
    for card_id in board["cards"].keys():
        if not card_id.startswith("card-"):
            continue
        suffix = card_id.removeprefix("card-")
        if suffix.isdigit():
            max_suffix = max(max_suffix, int(suffix))
    return f"card-{max_suffix + 1}"


def _find_column(board: dict, column_id: str) -> dict:
    for column in board["columns"]:
        if column["id"] == column_id:
            return column
    raise ValueError(f"Unknown column_id: {column_id}")


def _remove_card_from_columns(board: dict, card_id: str) -> None:
    for column in board["columns"]:
        if card_id in column["cardIds"]:
            column["cardIds"] = [existing_id for existing_id in column["cardIds"] if existing_id != card_id]


def _apply_board_operations(current_board: dict, operations: list[BoardOperation]) -> dict:
    board = deepcopy(current_board)

    for operation in operations:
        if operation.type == "create_card":
            column = _find_column(board, operation.column_id)
            new_card_id = _next_card_id(board)
            board["cards"][new_card_id] = {
                "id": new_card_id,
                "title": operation.title,
                "details": operation.details,
            }
            column["cardIds"].append(new_card_id)
            continue

        if operation.type == "edit_card":
            card = board["cards"].get(operation.card_id)
            if card is None:
                raise ValueError(f"Unknown card_id: {operation.card_id}")
            if operation.title is not None:
                card["title"] = operation.title
            if operation.details is not None:
                card["details"] = operation.details
            continue

        if operation.type == "move_card":
            if operation.card_id not in board["cards"]:
                raise ValueError(f"Unknown card_id: {operation.card_id}")

            destination = _find_column(board, operation.to_column_id)
            _remove_card_from_columns(board, operation.card_id)

            if operation.before_card_id is None:
                destination["cardIds"].append(operation.card_id)
                continue

            if operation.before_card_id not in destination["cardIds"]:
                raise ValueError(f"before_card_id must be in destination column: {operation.before_card_id}")

            insert_index = destination["cardIds"].index(operation.before_card_id)
            destination["cardIds"].insert(insert_index, operation.card_id)
            continue

        if operation.type == "delete_card":
            if operation.card_id not in board["cards"]:
                raise ValueError(f"Unknown card_id: {operation.card_id}")
            _remove_card_from_columns(board, operation.card_id)
            del board["cards"][operation.card_id]
            continue

        if operation.type == "rename_column":
            column = _find_column(board, operation.column_id)
            column["title"] = operation.title
            continue

    # Reuse BoardPayload validation before persisting the update.
    return BoardPayload.model_validate(board).model_dump()


def _get_session_history(request: Request) -> list[dict[str, str]]:
    session_token = request.cookies.get(SESSION_COOKIE)
    if not session_token or session_token not in SESSION_STORE:
        return []
    return SESSION_CHAT_HISTORY.setdefault(session_token, [])


def _frontend_file(path: str) -> Path:
    normalized = path.lstrip("/")
    candidate = FRONTEND_DIST_DIR / normalized

    if not candidate.resolve().is_relative_to(FRONTEND_DIST_DIR.resolve()):
        raise HTTPException(status_code=404, detail="Not found")

    if candidate.is_dir():
        return candidate / "index.html"
    if candidate.exists():
        return candidate
    return FRONTEND_DIST_DIR / "index.html"


def _current_user(request: Request) -> sqlite3.Row | None:
    session_token = request.cookies.get(SESSION_COOKIE)
    if not session_token:
        return None
    username = SESSION_STORE.get(session_token)
    return _get_user_by_username(username)


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


@app.post("/api/ai/connectivity")
def ai_connectivity(request: Request) -> dict[str, str | bool]:
    _require_api_user(request)

    try:
        response_text = run_connectivity_check()
    except MissingApiKeyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OpenAIConnectivityError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI connectivity failed: {exc}") from exc

    return {
        "ok": True,
        "model": get_openai_model(),
        "prompt": "2+2",
        "response": response_text,
    }


@app.post("/api/chat")
def chat(request: Request, payload: ChatMessagePayload) -> dict[str, str | bool | None]:
    user = _require_api_user(request)
    board = _read_user_board(user["id"])
    history = _get_session_history(request)

    try:
        raw_result = run_structured_chat(
            board=board,
            user_prompt=payload.prompt,
            conversation_history=history,
        )
        result = AIChatResultPayload.model_validate(raw_result)
    except MissingApiKeyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OpenAIChatError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI chat failed: {exc}") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Invalid AI structured response: {exc}") from exc

    board_updated = False
    update_error = None
    if result.board_update is not None:
        try:
            updated_board = _apply_board_operations(board, result.board_update.operations)
            _write_user_board(user["id"], updated_board)
            board_updated = True
        except ValueError as exc:
            board_updated = False
            update_error = str(exc)
            logger.error("Board operation failed: %s", update_error)

    history.append({"role": "user", "content": payload.prompt})
    history.append({"role": "assistant", "content": result.assistant_message})
    history[:] = history[-MAX_CHAT_HISTORY_MESSAGES:]

    return {
        "assistant_message": result.assistant_message,
        "board_updated": board_updated,
        "update_error": update_error,
    }


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


@app.post("/auth/logout", include_in_schema=False)
def logout(request: Request) -> RedirectResponse:
    session_token = request.cookies.get(SESSION_COOKIE)
    if session_token:
        SESSION_STORE.pop(session_token, None)
        SESSION_CHAT_HISTORY.pop(session_token, None)

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
