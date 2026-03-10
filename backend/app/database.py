import copy
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


def _table_exists(connection: sqlite3.Connection, table_name: str) -> bool:
    row = connection.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,),
    ).fetchone()
    return row is not None


def _migrate_users_table(connection: sqlite3.Connection) -> set[str]:
    user_columns = _table_columns(connection, "users")

    if "password_hash" not in user_columns:
        connection.execute("ALTER TABLE users ADD COLUMN password_hash TEXT")
        user_columns.add("password_hash")

    if "password_salt" not in user_columns:
        connection.execute("ALTER TABLE users ADD COLUMN password_salt TEXT")
        user_columns.add("password_salt")

    if "display_name" not in user_columns:
        connection.execute(
            "ALTER TABLE users ADD COLUMN display_name TEXT NOT NULL DEFAULT ''"
        )
        user_columns.add("display_name")

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


def _migrate_boards_table(connection: sqlite3.Connection) -> None:
    board_columns = _table_columns(connection, "boards")

    if "description" not in board_columns:
        connection.execute(
            "ALTER TABLE boards ADD COLUMN description TEXT NOT NULL DEFAULT ''"
        )

    if "archived" not in board_columns:
        connection.execute(
            "ALTER TABLE boards ADD COLUMN archived INTEGER NOT NULL DEFAULT 0"
        )

    # Remove UNIQUE constraint on user_id if it exists.
    # SQLite requires table recreation to drop constraints.
    index_info = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name='boards'"
    ).fetchone()
    if index_info and "UNIQUE" in (index_info["sql"] or ""):
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS boards_new (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              title TEXT NOT NULL DEFAULT 'Kanban Board',
              description TEXT NOT NULL DEFAULT '',
              board_json TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
              updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
              FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            INSERT INTO boards_new (id, user_id, title, board_json, created_at, updated_at)
            SELECT id, user_id, title, board_json, created_at, updated_at FROM boards;

            DROP TABLE boards;

            ALTER TABLE boards_new RENAME TO boards;
            """
        )

    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id)"
    )


def initialize_database() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with db_connection() as connection:
        connection.executescript(
            """
            PRAGMA user_version = 3;

            CREATE TABLE IF NOT EXISTS users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              password_hash TEXT NOT NULL,
              password_salt TEXT NOT NULL,
              display_name TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
              updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            );

            CREATE TABLE IF NOT EXISTS boards (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              user_id INTEGER NOT NULL,
              title TEXT NOT NULL DEFAULT 'Kanban Board',
              description TEXT NOT NULL DEFAULT '',
              archived INTEGER NOT NULL DEFAULT 0,
              board_json TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
              updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
              FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS activity_log (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              board_id INTEGER NOT NULL,
              user_id INTEGER NOT NULL,
              action TEXT NOT NULL,
              detail TEXT NOT NULL DEFAULT '',
              created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
              FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
              FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
            CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);
            CREATE INDEX IF NOT EXISTS idx_activity_board_id ON activity_log(board_id);
            """
        )

        user_columns = _migrate_users_table(connection)
        if _table_exists(connection, "boards"):
            _migrate_boards_table(connection)

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

        # Seed a default board only if the MVP user has none
        existing_boards = connection.execute(
            "SELECT id FROM boards WHERE user_id = ?",
            (user_id_row["id"],),
        ).fetchone()

        if existing_boards is None:
            connection.execute(
                """
                INSERT INTO boards (user_id, title, description, board_json)
                VALUES (?, 'My First Board', 'Default project board', ?)
                """,
                (user_id_row["id"], json.dumps(INITIAL_BOARD)),
            )


# --- User operations ---


def get_user_by_username(username: str | None) -> sqlite3.Row | None:
    if not username:
        return None

    with db_connection() as connection:
        return connection.execute(
            "SELECT id, username, password_hash, password_salt, display_name FROM users WHERE username = ?",
            (username,),
        ).fetchone()


def verify_credentials(username: str, password: str) -> bool:
    user = get_user_by_username(username)
    if user is None:
        return False
    expected_hash = hash_password(password, user["password_salt"])
    return user["password_hash"] == expected_hash


def create_user(username: str, password: str, display_name: str = "") -> int:
    salt = secrets.token_hex(16)
    hashed = hash_password(password, salt)

    with db_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO users (username, password_hash, password_salt, display_name)
            VALUES (?, ?, ?, ?)
            """,
            (username, hashed, salt, display_name),
        )
        user_id = cursor.lastrowid

        # Create a default board for the new user
        connection.execute(
            """
            INSERT INTO boards (user_id, title, description, board_json)
            VALUES (?, 'My First Board', 'Your default project board', ?)
            """,
            (user_id, json.dumps(INITIAL_BOARD)),
        )

        return user_id


def update_user_display_name(user_id: int, display_name: str) -> None:
    with db_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET display_name = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE id = ?
            """,
            (display_name, user_id),
        )


def change_user_password(user_id: int, new_password: str) -> None:
    salt = secrets.token_hex(16)
    hashed = hash_password(new_password, salt)
    with db_connection() as connection:
        connection.execute(
            """
            UPDATE users
            SET password_hash = ?, password_salt = ?,
                updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE id = ?
            """,
            (hashed, salt, user_id),
        )


def username_exists(username: str) -> bool:
    with db_connection() as connection:
        row = connection.execute(
            "SELECT 1 FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return row is not None


# --- Board operations ---


def list_user_boards(user_id: int) -> list[dict]:
    with db_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, title, description, created_at, updated_at
            FROM boards
            WHERE user_id = ?
            ORDER BY updated_at DESC
            """,
            (user_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def list_user_boards_with_counts(user_id: int, include_archived: bool = False) -> list[dict]:
    archive_filter = "" if include_archived else " AND archived = 0"
    with db_connection() as connection:
        rows = connection.execute(
            f"""
            SELECT id, title, description, archived, board_json, created_at, updated_at
            FROM boards
            WHERE user_id = ?{archive_filter}
            ORDER BY updated_at DESC
            """,
            (user_id,),
        ).fetchall()

    boards = []
    for row in rows:
        board_data = json.loads(row["board_json"])
        boards.append({
            "id": row["id"],
            "title": row["title"],
            "description": row["description"],
            "archived": bool(row["archived"]),
            "card_count": len(board_data.get("cards", {})),
            "column_count": len(board_data.get("columns", [])),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        })
    return boards


BOARD_TEMPLATE_DATA: dict[str, dict] = {
    "blank": {
        "columns": [
            {"id": "col-backlog", "title": "Backlog", "cardIds": []},
            {"id": "col-progress", "title": "In Progress", "cardIds": []},
            {"id": "col-review", "title": "Review", "cardIds": []},
            {"id": "col-done", "title": "Done", "cardIds": []},
        ],
        "cards": {},
    },
    "scrum": {
        "columns": [
            {"id": "col-backlog", "title": "Product Backlog", "cardIds": []},
            {"id": "col-sprint", "title": "Sprint Backlog", "cardIds": []},
            {"id": "col-progress", "title": "In Progress", "cardIds": []},
            {"id": "col-review", "title": "In Review", "cardIds": []},
            {"id": "col-testing", "title": "Testing", "cardIds": []},
            {"id": "col-done", "title": "Done", "cardIds": []},
        ],
        "cards": {},
    },
    "bug_tracking": {
        "columns": [
            {"id": "col-reported", "title": "Reported", "cardIds": []},
            {"id": "col-confirmed", "title": "Confirmed", "cardIds": []},
            {"id": "col-fixing", "title": "Fixing", "cardIds": []},
            {"id": "col-testing", "title": "Testing", "cardIds": []},
            {"id": "col-closed", "title": "Closed", "cardIds": []},
        ],
        "cards": {},
    },
    "product_launch": {
        "columns": [
            {"id": "col-ideas", "title": "Ideas", "cardIds": []},
            {"id": "col-research", "title": "Research", "cardIds": []},
            {"id": "col-design", "title": "Design", "cardIds": []},
            {"id": "col-development", "title": "Development", "cardIds": []},
            {"id": "col-launch", "title": "Launch", "cardIds": []},
            {"id": "col-post", "title": "Post-Launch", "cardIds": []},
        ],
        "cards": {},
    },
}


def create_board(
    user_id: int,
    title: str,
    description: str = "",
    board_json: dict | None = None,
    template: str = "blank",
) -> dict:
    if board_json is None:
        board_json = copy.deepcopy(BOARD_TEMPLATE_DATA.get(template, BOARD_TEMPLATE_DATA["blank"]))

    with db_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO boards (user_id, title, description, board_json)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, title, description, json.dumps(board_json)),
        )
        row = connection.execute(
            "SELECT id, title, description, created_at, updated_at FROM boards WHERE id = ?",
            (cursor.lastrowid,),
        ).fetchone()
    return dict(row)


def get_board(board_id: int, user_id: int) -> dict:
    with db_connection() as connection:
        row = connection.execute(
            "SELECT id, title, description, board_json, user_id FROM boards WHERE id = ? AND user_id = ?",
            (board_id, user_id),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Board not found")
    return dict(row)


def read_board_data(board_id: int, user_id: int) -> dict:
    board_row = get_board(board_id, user_id)
    return json.loads(board_row["board_json"])


def write_board_data(board_id: int, user_id: int, board: dict) -> None:
    with db_connection() as connection:
        result = connection.execute(
            """
            UPDATE boards
            SET board_json = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE id = ? AND user_id = ?
            """,
            (json.dumps(board), board_id, user_id),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Board not found")


def update_board_meta(board_id: int, user_id: int, title: str | None = None, description: str | None = None) -> dict:
    with db_connection() as connection:
        updates = []
        params: list = []
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if not updates:
            raise HTTPException(status_code=400, detail="No fields to update")

        updates.append("updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')")
        params.extend([board_id, user_id])

        result = connection.execute(
            f"UPDATE boards SET {', '.join(updates)} WHERE id = ? AND user_id = ?",
            params,
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Board not found")

        row = connection.execute(
            "SELECT id, title, description, created_at, updated_at FROM boards WHERE id = ?",
            (board_id,),
        ).fetchone()
    return dict(row)


def archive_board(board_id: int, user_id: int, archived: bool = True) -> bool:
    with db_connection() as connection:
        result = connection.execute(
            """
            UPDATE boards
            SET archived = ?, updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
            WHERE id = ? AND user_id = ?
            """,
            (1 if archived else 0, board_id, user_id),
        )
        return result.rowcount > 0


def duplicate_board(board_id: int, user_id: int) -> dict:
    with db_connection() as connection:
        row = connection.execute(
            "SELECT title, description, board_json FROM boards WHERE id = ? AND user_id = ?",
            (board_id, user_id),
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=404, detail="Board not found")

    new_title = f"{row['title']} (copy)"
    return create_board(user_id, new_title, row["description"], json.loads(row["board_json"]))


def delete_board(board_id: int, user_id: int) -> bool:
    with db_connection() as connection:
        result = connection.execute(
            "DELETE FROM boards WHERE id = ? AND user_id = ?",
            (board_id, user_id),
        )
        return result.rowcount > 0


# Legacy compatibility wrappers (used by old single-board code paths)


def read_user_board(user_id: int) -> dict:
    with db_connection() as connection:
        row = connection.execute(
            "SELECT board_json FROM boards WHERE user_id = ? ORDER BY id LIMIT 1",
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
            WHERE user_id = ? AND id = (SELECT id FROM boards WHERE user_id = ? ORDER BY id LIMIT 1)
            """,
            (json.dumps(board), user_id, user_id),
        )

        if result.rowcount == 0:
            raise HTTPException(status_code=404, detail="Board not found")


# --- Activity log ---


def log_activity(board_id: int, user_id: int, action: str, detail: str = "") -> None:
    with db_connection() as connection:
        connection.execute(
            "INSERT INTO activity_log (board_id, user_id, action, detail) VALUES (?, ?, ?, ?)",
            (board_id, user_id, action, detail),
        )


def get_board_activity(board_id: int, user_id: int, limit: int = 50) -> list[dict]:
    with db_connection() as connection:
        # Verify board ownership
        board = connection.execute(
            "SELECT id FROM boards WHERE id = ? AND user_id = ?",
            (board_id, user_id),
        ).fetchone()
        if board is None:
            raise HTTPException(status_code=404, detail="Board not found")

        rows = connection.execute(
            """
            SELECT a.id, a.action, a.detail, a.created_at, u.username, u.display_name
            FROM activity_log a
            JOIN users u ON u.id = a.user_id
            WHERE a.board_id = ?
            ORDER BY a.created_at DESC
            LIMIT ?
            """,
            (board_id, limit),
        ).fetchall()
    return [dict(row) for row in rows]
