import copy
from pathlib import Path

from conftest import make_test_client, login_test_client
from app.routes import api as api_routes


def test_chat_requires_authentication(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.post("/api/chat", json={"prompt": "hello"})

    assert response.status_code == 401


def test_chat_no_update_returns_message(tmp_path: Path, monkeypatch) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    monkeypatch.setattr(
        api_routes,
        "run_structured_chat",
        lambda **_: {"assistant_message": "No changes", "board_update": None},
    )

    response = client.post("/api/chat", json={"prompt": "status update"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["assistant_message"] == "No changes"
    assert payload["board_updated"] is False


def test_chat_update_is_applied_atomically(tmp_path: Path, monkeypatch) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    monkeypatch.setattr(
        api_routes,
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
    client = make_test_client(tmp_path)
    login_test_client(client)

    before_board = client.get("/api/board").json()["board"]

    monkeypatch.setattr(
        api_routes,
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
    client = make_test_client(tmp_path)
    login_test_client(client)

    observed_history: list[list[dict[str, str]]] = []

    def _fake_chat(*, conversation_history, **_kwargs):
        observed_history.append(copy.deepcopy(conversation_history))
        return {"assistant_message": "ok", "board_update": None}

    monkeypatch.setattr(api_routes, "run_structured_chat", _fake_chat)

    first_response = client.post("/api/chat", json={"prompt": "first"})
    second_response = client.post("/api/chat", json={"prompt": "second"})

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert observed_history[0] == []
    assert len(observed_history[1]) == 2
    assert observed_history[1][0]["role"] == "user"
    assert observed_history[1][1]["role"] == "assistant"
