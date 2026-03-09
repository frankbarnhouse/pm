from pathlib import Path

from conftest import make_test_client, login_test_client


def _setup_board_with_card(tmp_path: Path):
    """Create a board with a known card and return (client, board_id, card_id)."""
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards", json={"title": "Test Board"})
    board_id = resp.json()["board"]["id"]

    board_data = {
        "columns": [
            {"id": "col-1", "title": "Todo", "cardIds": ["card-1"]},
        ],
        "cards": {
            "card-1": {"id": "card-1", "title": "Task A", "details": "Details"},
        },
    }
    client.put(f"/api/boards/{board_id}", json=board_data)
    return client, board_id, "card-1"


def test_add_comment_requires_auth(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    response = client.post("/api/boards/1/cards/card-1/comments", json={"text": "Hello"})
    assert response.status_code == 401


def test_add_comment_success(tmp_path: Path) -> None:
    client, board_id, card_id = _setup_board_with_card(tmp_path)

    response = client.post(f"/api/boards/{board_id}/cards/{card_id}/comments", json={"text": "Great work"})
    assert response.status_code == 201
    comment = response.json()["comment"]
    assert comment["text"] == "Great work"
    assert comment["author"] == "user"
    assert "id" in comment


def test_add_comment_persisted(tmp_path: Path) -> None:
    client, board_id, card_id = _setup_board_with_card(tmp_path)

    client.post(f"/api/boards/{board_id}/cards/{card_id}/comments", json={"text": "Persisted"})

    board = client.get(f"/api/boards/{board_id}").json()["board"]
    comments = board["cards"][card_id]["comments"]
    assert len(comments) == 1
    assert comments[0]["text"] == "Persisted"


def test_add_comment_empty_text_rejected(tmp_path: Path) -> None:
    client, board_id, card_id = _setup_board_with_card(tmp_path)

    response = client.post(f"/api/boards/{board_id}/cards/{card_id}/comments", json={"text": ""})
    assert response.status_code == 422


def test_delete_comment_success(tmp_path: Path) -> None:
    client, board_id, card_id = _setup_board_with_card(tmp_path)

    resp = client.post(f"/api/boards/{board_id}/cards/{card_id}/comments", json={"text": "To delete"})
    comment_id = resp.json()["comment"]["id"]

    del_resp = client.delete(f"/api/boards/{board_id}/cards/{card_id}/comments/{comment_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True

    board = client.get(f"/api/boards/{board_id}").json()["board"]
    assert len(board["cards"][card_id].get("comments", [])) == 0


def test_delete_comment_unknown_card_returns_404(tmp_path: Path) -> None:
    client, board_id, _ = _setup_board_with_card(tmp_path)

    response = client.delete(f"/api/boards/{board_id}/cards/card-missing/comments/cmt-1")
    assert response.status_code == 404


def test_multiple_comments_on_same_card(tmp_path: Path) -> None:
    client, board_id, card_id = _setup_board_with_card(tmp_path)

    client.post(f"/api/boards/{board_id}/cards/{card_id}/comments", json={"text": "First"})
    client.post(f"/api/boards/{board_id}/cards/{card_id}/comments", json={"text": "Second"})

    board = client.get(f"/api/boards/{board_id}").json()["board"]
    comments = board["cards"][card_id]["comments"]
    assert len(comments) == 2
    assert comments[0]["text"] == "First"
    assert comments[1]["text"] == "Second"
