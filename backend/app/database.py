import hashlib
import json
import secrets
import sqlite3
from pathlib import Path

from fastapi import HTTPException

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "app.db"

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


def hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 100000
    ).hex()


def db_connection() -> sqlite3.Connection:
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
            hashed = hash_password(row["password_plaintext"], salt)
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


def initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with db_connection() as connection:
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
        hashed = hash_password(MVP_PASSWORD, salt)

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


def get_user_by_username(username: str | None) -> sqlite3.Row | None:
    if not username:
        return None

    with db_connection() as connection:
        return connection.execute(
            "SELECT id, username, password_hash, password_salt FROM users WHERE username = ?",
            (username,),
        ).fetchone()


def verify_credentials(username: str, password: str) -> bool:
    user = get_user_by_username(username)
    if user is None:
        return False
    expected_hash = hash_password(password, user["password_salt"])
    return user["password_hash"] == expected_hash


def read_user_board(user_id: int) -> dict:
    with db_connection() as connection:
        row = connection.execute(
            "SELECT board_json FROM boards WHERE user_id = ?",
            (user_id,),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return json.loads(row["board_json"])


def write_user_board(user_id: int, board: dict) -> None:
    with db_connection() as connection:
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
