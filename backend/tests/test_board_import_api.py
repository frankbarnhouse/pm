from pathlib import Path

from conftest import make_test_client, login_test_client


def _valid_board_data() -> dict:
    return {
        "columns": [
            {"id": "col-1", "title": "Todo", "cardIds": ["card-1"]},
        ],
        "cards": {
            "card-1": {"id": "card-1", "title": "Task", "details": "Details"},
        },
    }


def test_import_board_requires_auth(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    response = client.post("/api/boards/import", json={
        "title": "Imported", "board": _valid_board_data(),
    })
    assert response.status_code == 401


def test_import_board_success(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.post("/api/boards/import", json={
        "title": "Imported Board",
        "description": "From export",
        "board": _valid_board_data(),
    })
    assert response.status_code == 201
    board = response.json()["board"]
    assert board["title"] == "Imported Board"
    assert board["description"] == "From export"


def test_import_board_appears_in_list(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    client.post("/api/boards/import", json={
        "title": "Imported", "board": _valid_board_data(),
    })

    boards = client.get("/api/boards").json()["boards"]
    titles = [b["title"] for b in boards]
    assert "Imported" in titles


def test_import_board_data_readable(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards/import", json={
        "title": "Imported", "board": _valid_board_data(),
    })
    board_id = resp.json()["board"]["id"]

    data = client.get(f"/api/boards/{board_id}").json()
    assert data["board"]["cards"]["card-1"]["title"] == "Task"


def test_import_board_invalid_data_rejected(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.post("/api/boards/import", json={
        "title": "Bad",
        "board": {"columns": [], "cards": {"card-1": {"id": "card-1", "title": "X", "details": "Y"}}},
    })
    assert response.status_code == 422


def test_import_board_missing_title_rejected(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.post("/api/boards/import", json={
        "title": "",
        "board": _valid_board_data(),
    })
    assert response.status_code == 422
