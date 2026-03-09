from pathlib import Path

from conftest import make_test_client, login_test_client
from app.routes import api as api_routes


def _get_first_board_id(client) -> int:
    response = client.get("/api/boards")
    return response.json()["boards"][0]["id"]


def test_board_chat_requires_authentication(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.post("/api/boards/1/chat", json={"prompt": "hello"})

    assert response.status_code == 401


def test_board_chat_returns_message(tmp_path: Path, monkeypatch) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)
    board_id = _get_first_board_id(client)

    monkeypatch.setattr(
        api_routes,
        "run_structured_chat",
        lambda **_: {"assistant_message": "All good", "board_update": None},
    )

    response = client.post(f"/api/boards/{board_id}/chat", json={"prompt": "status"})

    assert response.status_code == 200
    assert response.json()["assistant_message"] == "All good"
    assert response.json()["board_updated"] is False


def test_board_chat_applies_update(tmp_path: Path, monkeypatch) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)
    board_id = _get_first_board_id(client)

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
                        "title": "Chat task",
                        "details": "From board chat",
                    }
                ]
            },
        },
    )

    response = client.post(f"/api/boards/{board_id}/chat", json={"prompt": "add task"})

    assert response.status_code == 200
    assert response.json()["board_updated"] is True

    # Verify the board was updated
    board_data = client.get(f"/api/boards/{board_id}").json()["board"]
    assert "card-9" in board_data["cards"]
    assert board_data["cards"]["card-9"]["title"] == "Chat task"


def test_board_chat_wrong_board_returns_404(tmp_path: Path, monkeypatch) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.post("/api/boards/99999/chat", json={"prompt": "hello"})

    assert response.status_code == 404


def test_board_chat_rejects_other_users_board(tmp_path: Path, monkeypatch) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)
    board_id = _get_first_board_id(client)

    # Logout and register as another user
    client.post("/auth/logout", follow_redirects=False)
    client.post(
        "/auth/register",
        data={"username": "attacker", "password": "password"},
        follow_redirects=False,
    )

    monkeypatch.setattr(
        api_routes,
        "run_structured_chat",
        lambda **_: {"assistant_message": "ok", "board_update": None},
    )

    response = client.post(f"/api/boards/{board_id}/chat", json={"prompt": "hello"})

    assert response.status_code == 404
