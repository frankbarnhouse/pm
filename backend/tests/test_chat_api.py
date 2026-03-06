import copy
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import main


def _make_client(tmp_path: Path) -> TestClient:
    dist_dir = tmp_path / "frontend_dist"
    dist_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text("<html><body>Kanban Studio</body></html>")

    db_path = tmp_path / "data" / "app.db"
    main.FRONTEND_DIST_DIR = dist_dir
    main.DB_PATH = db_path
    main.SESSION_CHAT_HISTORY.clear()
    main._initialize_database()

    return TestClient(main.app)


def _login(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        data={"username": "user", "password": "password"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_chat_requires_authentication(tmp_path: Path) -> None:
    client = _make_client(tmp_path)

    response = client.post("/api/chat", json={"prompt": "hello"})

    assert response.status_code == 401


def test_chat_no_update_returns_message(tmp_path: Path, monkeypatch) -> None:
    client = _make_client(tmp_path)
    _login(client)

    monkeypatch.setattr(
        main,
        "run_structured_chat",
        lambda **_: {"assistant_message": "No changes", "board_update": None},
    )

    response = client.post("/api/chat", json={"prompt": "status update"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["assistant_message"] == "No changes"
    assert payload["board_updated"] is False


def test_chat_update_is_applied_atomically(tmp_path: Path, monkeypatch) -> None:
    client = _make_client(tmp_path)
    _login(client)

    monkeypatch.setattr(
        main,
        "run_structured_chat",
        lambda **_: {
            "assistant_message": "Added card",
            "board_update": {
                "operations": [
                    {
                        "type": "create_card",
                        "column_id": "col-backlog",
                        "title": "Generated task",
                        "details": "From AI",
                    }
                ]
            },
        },
    )

    response = client.post("/api/chat", json={"prompt": "add a task"})

    assert response.status_code == 200
    assert response.json()["board_updated"] is True

    board_response = client.get("/api/board")
    board = board_response.json()["board"]
    assert "card-9" in board["cards"]
    assert board["cards"]["card-9"]["title"] == "Generated task"


def test_chat_invalid_update_is_rejected_without_partial_write(tmp_path: Path, monkeypatch) -> None:
    client = _make_client(tmp_path)
    _login(client)

    before_board = client.get("/api/board").json()["board"]

    monkeypatch.setattr(
        main,
        "run_structured_chat",
        lambda **_: {
            "assistant_message": "Tried update",
            "board_update": {
                "operations": [
                    {
                        "type": "edit_card",
                        "card_id": "missing-card",
                        "title": "Will fail",
                    }
                ]
            },
        },
    )

    response = client.post("/api/chat", json={"prompt": "edit card"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["assistant_message"] == "Tried update"
    assert payload["board_updated"] is False

    after_board = client.get("/api/board").json()["board"]
    assert after_board == before_board


def test_chat_uses_session_history(tmp_path: Path, monkeypatch) -> None:
    client = _make_client(tmp_path)
    _login(client)

    observed_history: list[list[dict[str, str]]] = []

    def _fake_chat(*, conversation_history, **_kwargs):
        observed_history.append(copy.deepcopy(conversation_history))
        return {"assistant_message": "ok", "board_update": None}

    monkeypatch.setattr(main, "run_structured_chat", _fake_chat)

    first_response = client.post("/api/chat", json={"prompt": "first"})
    second_response = client.post("/api/chat", json={"prompt": "second"})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert observed_history[0] == []
    assert len(observed_history[1]) == 2
    assert observed_history[1][0]["role"] == "user"
    assert observed_history[1][1]["role"] == "assistant"
