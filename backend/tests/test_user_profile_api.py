from pathlib import Path

from conftest import make_test_client, login_test_client


def test_me_requires_authentication(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.get("/api/me")

    assert response.status_code == 401


def test_me_returns_user_info(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.get("/api/me")

    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "user"
    assert "id" in payload
    assert "display_name" in payload


def test_me_returns_registered_user_info(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    client.post(
        "/auth/register",
        data={"username": "alice", "password": "secret", "display_name": "Alice W"},
        follow_redirects=False,
    )

    response = client.get("/api/me")

    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "alice"
    assert payload["display_name"] == "Alice W"


def test_boards_list_includes_card_and_column_counts(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.get("/api/boards")

    assert response.status_code == 200
    boards = response.json()["boards"]
    assert len(boards) > 0
    board = boards[0]
    assert "card_count" in board
    assert "column_count" in board
    assert board["card_count"] == 8  # initial board has 8 cards
    assert board["column_count"] == 5  # initial board has 5 columns


def test_new_board_has_zero_card_count(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    client.post("/api/boards", json={"title": "Empty Board"})

    boards = client.get("/api/boards").json()["boards"]
    empty_board = next(b for b in boards if b["title"] == "Empty Board")
    assert empty_board["card_count"] == 0
    assert empty_board["column_count"] == 4  # default new board has 4 columns
