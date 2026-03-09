from pathlib import Path

from conftest import make_test_client, login_test_client


def _setup_board_with_card(tmp_path: Path):
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards", json={"title": "Checklist Board"})
    board_id = resp.json()["board"]["id"]

    board_data = {
        "columns": [{"id": "col-1", "title": "Todo", "cardIds": ["card-1"]}],
        "cards": {"card-1": {"id": "card-1", "title": "Task", "details": "D"}},
    }
    client.put(f"/api/boards/{board_id}", json=board_data)
    return client, board_id, "card-1"


def test_add_checklist_item_requires_auth(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    response = client.post("/api/boards/1/cards/card-1/checklist", json={"text": "Item"})
    assert response.status_code == 401


def test_add_checklist_item_success(tmp_path: Path) -> None:
    client, board_id, card_id = _setup_board_with_card(tmp_path)

    response = client.post(f"/api/boards/{board_id}/cards/{card_id}/checklist", json={"text": "Step 1"})
    assert response.status_code == 201
    item = response.json()["item"]
    assert item["text"] == "Step 1"
    assert item["done"] is False


def test_add_checklist_item_persisted(tmp_path: Path) -> None:
    client, board_id, card_id = _setup_board_with_card(tmp_path)

    client.post(f"/api/boards/{board_id}/cards/{card_id}/checklist", json={"text": "Persisted"})

    board = client.get(f"/api/boards/{board_id}").json()["board"]
    checklist = board["cards"][card_id]["checklist"]
    assert len(checklist) == 1
    assert checklist[0]["text"] == "Persisted"


def test_add_checklist_item_empty_text_rejected(tmp_path: Path) -> None:
    client, board_id, card_id = _setup_board_with_card(tmp_path)

    response = client.post(f"/api/boards/{board_id}/cards/{card_id}/checklist", json={"text": ""})
    assert response.status_code == 422


def test_toggle_checklist_item_success(tmp_path: Path) -> None:
    client, board_id, card_id = _setup_board_with_card(tmp_path)

    resp = client.post(f"/api/boards/{board_id}/cards/{card_id}/checklist", json={"text": "Toggle"})
    item_id = resp.json()["item"]["id"]

    toggle_resp = client.post(f"/api/boards/{board_id}/cards/{card_id}/checklist/{item_id}/toggle")
    assert toggle_resp.status_code == 200
    assert toggle_resp.json()["item"]["done"] is True

    toggle_resp2 = client.post(f"/api/boards/{board_id}/cards/{card_id}/checklist/{item_id}/toggle")
    assert toggle_resp2.json()["item"]["done"] is False


def test_toggle_checklist_unknown_item_404(tmp_path: Path) -> None:
    client, board_id, card_id = _setup_board_with_card(tmp_path)

    response = client.post(f"/api/boards/{board_id}/cards/{card_id}/checklist/chk-missing/toggle")
    assert response.status_code == 404


def test_delete_checklist_item_success(tmp_path: Path) -> None:
    client, board_id, card_id = _setup_board_with_card(tmp_path)

    resp = client.post(f"/api/boards/{board_id}/cards/{card_id}/checklist", json={"text": "Delete me"})
    item_id = resp.json()["item"]["id"]

    del_resp = client.delete(f"/api/boards/{board_id}/cards/{card_id}/checklist/{item_id}")
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted"] is True

    board = client.get(f"/api/boards/{board_id}").json()["board"]
    assert len(board["cards"][card_id].get("checklist", [])) == 0


def test_delete_checklist_unknown_item_404(tmp_path: Path) -> None:
    client, board_id, card_id = _setup_board_with_card(tmp_path)

    response = client.delete(f"/api/boards/{board_id}/cards/{card_id}/checklist/chk-missing")
    assert response.status_code == 404
