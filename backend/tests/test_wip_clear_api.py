from pathlib import Path

from conftest import make_test_client, login_test_client


def _setup_board(tmp_path: Path, columns=None, cards=None):
    """Create a board with given data and return (client, board_id)."""
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards", json={"title": "Test Board"})
    board_id = resp.json()["board"]["id"]

    board_data = {
        "columns": columns or [
            {"id": "col-1", "title": "Todo", "cardIds": ["card-1", "card-2"]},
            {"id": "col-2", "title": "Done", "cardIds": []},
        ],
        "cards": cards or {
            "card-1": {"id": "card-1", "title": "Task A", "details": "A"},
            "card-2": {"id": "card-2", "title": "Task B", "details": "B"},
        },
    }
    client.put(f"/api/boards/{board_id}", json=board_data)
    return client, board_id


# --- WIP Limit API tests ---


def test_set_wip_limit_requires_auth(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    response = client.post("/api/boards/1/columns/col-1/wip-limit", json={"wip_limit": 3})
    assert response.status_code == 401


def test_set_wip_limit_success(tmp_path: Path) -> None:
    client, board_id = _setup_board(tmp_path)
    response = client.post(f"/api/boards/{board_id}/columns/col-1/wip-limit", json={"wip_limit": 5})
    assert response.status_code == 200
    assert response.json()["wip_limit"] == 5

    # Verify the limit persisted
    board = client.get(f"/api/boards/{board_id}").json()["board"]
    col = next(c for c in board["columns"] if c["id"] == "col-1")
    assert col["wip_limit"] == 5


def test_set_wip_limit_to_null(tmp_path: Path) -> None:
    client, board_id = _setup_board(tmp_path)
    # Set a limit first
    client.post(f"/api/boards/{board_id}/columns/col-1/wip-limit", json={"wip_limit": 3})
    # Remove it
    response = client.post(f"/api/boards/{board_id}/columns/col-1/wip-limit", json={"wip_limit": None})
    assert response.status_code == 200
    assert response.json()["wip_limit"] is None


def test_set_wip_limit_unknown_column(tmp_path: Path) -> None:
    client, board_id = _setup_board(tmp_path)
    response = client.post(f"/api/boards/{board_id}/columns/col-missing/wip-limit", json={"wip_limit": 3})
    assert response.status_code == 400


# --- Clear Column API tests ---


def test_clear_column_requires_auth(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    response = client.post("/api/boards/1/columns/col-1/clear")
    assert response.status_code == 401


def test_clear_column_success(tmp_path: Path) -> None:
    client, board_id = _setup_board(tmp_path)
    response = client.post(f"/api/boards/{board_id}/columns/col-1/clear")
    assert response.status_code == 200
    assert response.json()["cleared"] is True

    # Verify cards removed
    board = client.get(f"/api/boards/{board_id}").json()["board"]
    col = next(c for c in board["columns"] if c["id"] == "col-1")
    assert col["cardIds"] == []
    assert "card-1" not in board["cards"]
    assert "card-2" not in board["cards"]


def test_clear_column_unknown(tmp_path: Path) -> None:
    client, board_id = _setup_board(tmp_path)
    response = client.post(f"/api/boards/{board_id}/columns/col-missing/clear")
    assert response.status_code == 404
