import json
from pathlib import Path

from conftest import make_test_client, login_test_client


def test_stats_requires_auth(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.get("/api/boards/1/stats")

    assert response.status_code == 401


def test_stats_returns_counts(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    response = client.get(f"/api/boards/{board_id}/stats")

    assert response.status_code == 200
    stats = response.json()
    assert stats["total_cards"] == 8
    assert stats["total_columns"] == 5
    assert stats["overdue_count"] == 0
    assert "by_priority" in stats
    assert stats["by_priority"]["none"] == 8
    assert "cards_per_column" in stats
    assert len(stats["cards_per_column"]) == 5


def test_stats_counts_priority(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    # Update board with cards that have priorities
    board_data = client.get(f"/api/boards/{board_id}").json()["board"]
    board_data["cards"]["card-1"]["priority"] = "high"
    board_data["cards"]["card-2"]["priority"] = "high"
    board_data["cards"]["card-3"]["priority"] = "medium"
    client.put(f"/api/boards/{board_id}", json=board_data)

    stats = client.get(f"/api/boards/{board_id}/stats").json()
    assert stats["by_priority"]["high"] == 2
    assert stats["by_priority"]["medium"] == 1
    assert stats["by_priority"]["none"] == 5


def test_stats_counts_overdue(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    board_data = client.get(f"/api/boards/{board_id}").json()["board"]
    board_data["cards"]["card-1"]["due_date"] = "2020-01-01"
    board_data["cards"]["card-2"]["due_date"] = "2020-06-15"
    board_data["cards"]["card-3"]["due_date"] = "2099-12-31"
    client.put(f"/api/boards/{board_id}", json=board_data)

    stats = client.get(f"/api/boards/{board_id}/stats").json()
    assert stats["overdue_count"] == 2


def test_stats_nonexistent_board_returns_404(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.get("/api/boards/99999/stats")
    assert response.status_code == 404


def test_stats_cards_per_column(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    boards = client.get("/api/boards").json()["boards"]
    board_id = boards[0]["id"]

    stats = client.get(f"/api/boards/{board_id}/stats").json()
    col_counts = {c["title"]: c["count"] for c in stats["cards_per_column"]}
    assert col_counts["Backlog"] == 2
    assert col_counts["Done"] == 2
    assert col_counts["Discovery"] == 1
