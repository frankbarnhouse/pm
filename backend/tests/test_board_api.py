import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from conftest import make_test_client, login_test_client
from app import main


def test_db_is_created_and_seeded_on_startup(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "app.db"
    client = make_test_client(tmp_path)

    client.get("/api/health")

    assert db_path.exists()

    with sqlite3.connect(db_path) as connection:
        user_row = connection.execute(
            "SELECT username FROM users WHERE username = ?",
            ("user",),
        ).fetchone()
        assert user_row is not None

        board_row = connection.execute(
            "SELECT board_json FROM boards"
        ).fetchone()
        assert board_row is not None
        assert "columns" in json.loads(board_row[0])


def test_legacy_users_schema_is_migrated(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "app.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE users (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT NOT NULL UNIQUE,
              password_plaintext TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
              updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            );

            INSERT INTO users (username, password_plaintext)
            VALUES ('user', 'password');
            """
        )

    main.DB_PATH = db_path
    main._initialize_database()

    with sqlite3.connect(db_path) as connection:
        user_row = connection.execute(
            "SELECT password_hash, password_salt FROM users WHERE username = ?",
            ("user",),
        ).fetchone()
        assert user_row is not None
        assert user_row[0]
        assert user_row[1]

    assert main._verify_credentials("user", "password")


def test_board_api_requires_authentication(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.get("/api/board")

    assert response.status_code == 401


def test_get_board_returns_persisted_board(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.get("/api/board")

    assert response.status_code == 200
    payload = response.json()
    assert "board" in payload
    assert len(payload["board"]["columns"]) == 5


def test_put_board_overwrites_persisted_board(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    update_payload = {
        "columns": [
            {"id": "col-backlog", "title": "Backlog", "cardIds": ["card-1"]},
            {"id": "col-done", "title": "Done", "cardIds": []},
        ],
        "cards": {
            "card-1": {
                "id": "card-1",
                "title": "Updated task",
                "details": "Persisted detail",
            }
        },
    }

    put_response = client.put("/api/board", json=update_payload)
    assert put_response.status_code == 200

    get_response = client.get("/api/board")
    assert get_response.status_code == 200

    board = get_response.json()["board"]
    assert board["cards"]["card-1"]["title"] == "Updated task"
    assert board["columns"][0]["cardIds"] == ["card-1"]


def test_put_board_rejects_invalid_board_shape(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    invalid_payload = {
        "columns": [
            {"id": "col-a", "title": "A", "cardIds": ["missing-card"]},
        ],
        "cards": {},
    }

    response = client.put("/api/board", json=invalid_payload)

    assert response.status_code == 422
