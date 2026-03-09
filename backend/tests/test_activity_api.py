from pathlib import Path

from conftest import make_test_client, login_test_client


def test_activity_requires_auth(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    response = client.get("/api/boards/1/activity")
    assert response.status_code == 401


def test_activity_empty_initially(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    response = client.get(f"/api/boards/{board_id}/activity")
    assert response.status_code == 200
    assert response.json()["activity"] == []


def test_activity_logged_on_board_create(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards", json={"title": "Tracked Board"})
    board_id = resp.json()["board"]["id"]

    activity = client.get(f"/api/boards/{board_id}/activity").json()["activity"]
    assert len(activity) == 1
    assert activity[0]["action"] == "board_created"
    assert "Tracked Board" in activity[0]["detail"]


def test_activity_logged_on_board_update(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards", json={"title": "Log Test"})
    board_id = resp.json()["board"]["id"]

    board_data = {
        "columns": [{"id": "col-1", "title": "Todo", "cardIds": []}],
        "cards": {},
    }
    client.put(f"/api/boards/{board_id}", json=board_data)

    activity = client.get(f"/api/boards/{board_id}/activity").json()["activity"]
    actions = [a["action"] for a in activity]
    assert "board_updated" in actions


def test_activity_logged_on_comment(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards", json={"title": "Comment Log"})
    board_id = resp.json()["board"]["id"]

    board_data = {
        "columns": [{"id": "col-1", "title": "Todo", "cardIds": ["card-1"]}],
        "cards": {"card-1": {"id": "card-1", "title": "Task", "details": "D"}},
    }
    client.put(f"/api/boards/{board_id}", json=board_data)

    client.post(f"/api/boards/{board_id}/cards/card-1/comments", json={"text": "Noted"})

    activity = client.get(f"/api/boards/{board_id}/activity").json()["activity"]
    actions = [a["action"] for a in activity]
    assert "comment_added" in actions


def test_activity_includes_user_info(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards", json={"title": "User Info Test"})
    board_id = resp.json()["board"]["id"]

    activity = client.get(f"/api/boards/{board_id}/activity").json()["activity"]
    assert activity[0]["username"] == "user"


def test_activity_ordered_newest_first(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards", json={"title": "Order Test"})
    board_id = resp.json()["board"]["id"]

    board_data = {
        "columns": [{"id": "col-1", "title": "A", "cardIds": []}],
        "cards": {},
    }
    client.put(f"/api/boards/{board_id}", json=board_data)

    activity = client.get(f"/api/boards/{board_id}/activity").json()["activity"]
    assert len(activity) >= 2
    # Most recent first
    assert activity[0]["action"] == "board_updated"
    assert activity[1]["action"] == "board_created"
