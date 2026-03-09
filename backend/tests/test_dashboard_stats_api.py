from pathlib import Path

from conftest import make_test_client, login_test_client


def test_dashboard_stats_requires_auth(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.get("/api/dashboard/stats")

    assert response.status_code == 401


def test_dashboard_stats_returns_totals(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.get("/api/dashboard/stats")

    assert response.status_code == 200
    stats = response.json()
    assert stats["total_boards"] == 1
    assert stats["total_cards"] == 8  # seeded board has 8 cards
    assert stats["total_columns"] == 5  # seeded board has 5 columns


def test_dashboard_stats_with_multiple_boards(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    # Create a second board (gets 4 default empty columns)
    client.post("/api/boards", json={"title": "Board 2"})

    stats = client.get("/api/dashboard/stats").json()
    assert stats["total_boards"] == 2
    assert stats["total_cards"] == 8  # only seeded board has cards
    assert stats["total_columns"] == 9  # 5 + 4


def test_dashboard_stats_excludes_archived(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    client.post(f"/api/boards/{board_id}/archive")

    stats = client.get("/api/dashboard/stats").json()
    assert stats["total_boards"] == 0
    assert stats["total_cards"] == 0
