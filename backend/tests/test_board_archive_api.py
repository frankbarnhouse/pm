from pathlib import Path

from conftest import make_test_client, login_test_client


def test_archive_board(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    response = client.post(f"/api/boards/{board_id}/archive")
    assert response.status_code == 200
    assert response.json()["archived"] is True


def test_archived_board_hidden_by_default(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    client.post(f"/api/boards/{board_id}/archive")

    # Default listing should not show archived boards
    visible_boards = client.get("/api/boards").json()["boards"]
    assert len(visible_boards) == 0


def test_archived_board_visible_with_flag(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    client.post(f"/api/boards/{board_id}/archive")

    all_boards = client.get("/api/boards?include_archived=true").json()["boards"]
    assert len(all_boards) == 1
    assert all_boards[0]["archived"] is True


def test_unarchive_board(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    client.post(f"/api/boards/{board_id}/archive")
    assert len(client.get("/api/boards").json()["boards"]) == 0

    response = client.post(f"/api/boards/{board_id}/unarchive")
    assert response.status_code == 200
    assert response.json()["archived"] is False

    visible_boards = client.get("/api/boards").json()["boards"]
    assert len(visible_boards) == 1


def test_archive_nonexistent_board(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.post("/api/boards/99999/archive")
    assert response.status_code == 404


def test_archive_other_users_board(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    client.post("/auth/logout", follow_redirects=False)
    client.post(
        "/auth/register",
        data={"username": "other", "password": "secret"},
        follow_redirects=False,
    )

    response = client.post(f"/api/boards/{board_id}/archive")
    assert response.status_code == 404


def test_archived_board_still_accessible_by_id(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    client.post(f"/api/boards/{board_id}/archive")

    # Can still GET the board by ID even when archived
    response = client.get(f"/api/boards/{board_id}")
    assert response.status_code == 200


def test_board_list_shows_archived_flag(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    # Active board should have archived=False
    boards = client.get("/api/boards").json()["boards"]
    assert boards[0]["archived"] is False
