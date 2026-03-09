import json
from pathlib import Path

from conftest import make_test_client, login_test_client


def test_list_boards_requires_auth(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.get("/api/boards")

    assert response.status_code == 401


def test_list_boards_returns_seeded_board(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.get("/api/boards")

    assert response.status_code == 200
    boards = response.json()["boards"]
    assert len(boards) == 1
    assert boards[0]["title"] == "My First Board"
    assert "id" in boards[0]
    assert "created_at" in boards[0]
    assert "updated_at" in boards[0]


def test_create_board(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.post(
        "/api/boards",
        json={"title": "Sprint Board", "description": "Weekly sprint tracking"},
    )

    assert response.status_code == 201
    board = response.json()["board"]
    assert board["title"] == "Sprint Board"
    assert board["description"] == "Weekly sprint tracking"
    assert "id" in board

    # Should now have 2 boards
    list_response = client.get("/api/boards")
    assert len(list_response.json()["boards"]) == 2


def test_create_board_requires_title(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.post("/api/boards", json={"title": ""})

    assert response.status_code == 422


def test_get_board_by_id(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    response = client.get(f"/api/boards/{board_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == board_id
    assert data["title"] == "My First Board"
    assert "board" in data
    assert "columns" in data["board"]
    assert "cards" in data["board"]


def test_get_board_wrong_id_returns_404(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.get("/api/boards/99999")

    assert response.status_code == 404


def test_put_board_by_id(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    update_payload = {
        "columns": [
            {"id": "col-a", "title": "Todo", "cardIds": ["card-1"]},
            {"id": "col-b", "title": "Done", "cardIds": []},
        ],
        "cards": {
            "card-1": {"id": "card-1", "title": "Test task", "details": "Details"},
        },
    }

    response = client.put(f"/api/boards/{board_id}", json=update_payload)
    assert response.status_code == 200

    # Verify persisted
    get_response = client.get(f"/api/boards/{board_id}")
    board_data = get_response.json()["board"]
    assert board_data["cards"]["card-1"]["title"] == "Test task"


def test_patch_board_meta(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    response = client.patch(
        f"/api/boards/{board_id}",
        json={"title": "Renamed Board", "description": "Updated description"},
    )

    assert response.status_code == 200
    board = response.json()["board"]
    assert board["title"] == "Renamed Board"
    assert board["description"] == "Updated description"


def test_patch_board_meta_title_only(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    response = client.patch(f"/api/boards/{board_id}", json={"title": "New Title"})

    assert response.status_code == 200
    assert response.json()["board"]["title"] == "New Title"


def test_patch_board_meta_requires_fields(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    response = client.patch(f"/api/boards/{board_id}", json={})

    assert response.status_code == 422


def test_delete_board(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    # Create a second board
    create_response = client.post(
        "/api/boards", json={"title": "To Delete"}
    )
    board_id = create_response.json()["board"]["id"]

    response = client.delete(f"/api/boards/{board_id}")

    assert response.status_code == 200
    assert response.json()["deleted"] is True

    # Verify it's gone
    get_response = client.get(f"/api/boards/{board_id}")
    assert get_response.status_code == 404


def test_delete_nonexistent_board_returns_404(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.delete("/api/boards/99999")

    assert response.status_code == 404


def test_boards_are_isolated_per_user(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    # Register a second user
    client.post(
        "/auth/register",
        data={"username": "alice", "password": "secret123"},
        follow_redirects=False,
    )

    # Alice should only see her own board
    alice_boards = client.get("/api/boards").json()["boards"]
    assert len(alice_boards) == 1
    assert alice_boards[0]["title"] == "My First Board"

    # Create a board as Alice
    client.post("/api/boards", json={"title": "Alice Board"})
    assert len(client.get("/api/boards").json()["boards"]) == 2

    # Logout and login as default user
    client.post("/auth/logout", follow_redirects=False)
    login_test_client(client)

    # Default user should only see their board
    user_boards = client.get("/api/boards").json()["boards"]
    assert len(user_boards) == 1


def test_user_cannot_access_other_users_board(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    # Get default user's board id
    boards = client.get("/api/boards").json()["boards"]
    default_board_id = boards[0]["id"]

    # Logout, register as another user
    client.post("/auth/logout", follow_redirects=False)
    client.post(
        "/auth/register",
        data={"username": "mallory", "password": "password"},
        follow_redirects=False,
    )

    # Try to access default user's board
    response = client.get(f"/api/boards/{default_board_id}")
    assert response.status_code == 404


def test_board_list_ordered_by_updated_at(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    # Create two more boards
    client.post("/api/boards", json={"title": "Board B"})
    client.post("/api/boards", json={"title": "Board C"})

    boards = client.get("/api/boards").json()["boards"]
    assert len(boards) == 3
    # Most recently updated should be first
    assert boards[0]["title"] == "Board C"


def test_create_board_has_empty_columns(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    create_response = client.post(
        "/api/boards", json={"title": "Empty Board"}
    )
    board_id = create_response.json()["board"]["id"]

    board_data = client.get(f"/api/boards/{board_id}").json()["board"]
    assert len(board_data["columns"]) == 4
    assert board_data["cards"] == {}
    for col in board_data["columns"]:
        assert col["cardIds"] == []
