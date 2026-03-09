"""Integration tests exercising multi-step workflows across multiple API endpoints."""

from pathlib import Path

from conftest import make_test_client, login_test_client


def test_full_board_lifecycle(tmp_path: Path) -> None:
    """Create board, add cards via PUT, archive, unarchive, delete."""
    client = make_test_client(tmp_path)
    login_test_client(client)

    # Create
    resp = client.post("/api/boards", json={"title": "Sprint 1", "description": "Q1"})
    assert resp.status_code == 201
    board_id = resp.json()["board"]["id"]

    # Update board data
    board_data = {
        "columns": [
            {"id": "col-1", "title": "Todo", "cardIds": ["card-1"]},
            {"id": "col-2", "title": "Done", "cardIds": []},
        ],
        "cards": {
            "card-1": {"id": "card-1", "title": "Setup CI", "details": "Configure pipeline"},
        },
    }
    client.put(f"/api/boards/{board_id}", json=board_data)

    # Verify data persisted
    fetched = client.get(f"/api/boards/{board_id}").json()
    assert fetched["board"]["cards"]["card-1"]["title"] == "Setup CI"

    # Archive
    client.post(f"/api/boards/{board_id}/archive")
    boards = client.get("/api/boards").json()["boards"]
    assert all(b["id"] != board_id for b in boards)

    # Unarchive
    client.post(f"/api/boards/{board_id}/unarchive")
    boards = client.get("/api/boards").json()["boards"]
    assert any(b["id"] == board_id for b in boards)

    # Delete
    client.delete(f"/api/boards/{board_id}")
    boards = client.get("/api/boards").json()["boards"]
    assert all(b["id"] != board_id for b in boards)


def test_duplicate_then_modify_independently(tmp_path: Path) -> None:
    """Duplicate a board and verify changes to duplicate don't affect original."""
    client = make_test_client(tmp_path)
    login_test_client(client)

    # Get seeded board
    boards = client.get("/api/boards").json()["boards"]
    original_id = boards[0]["id"]
    original_data = client.get(f"/api/boards/{original_id}").json()["board"]

    # Duplicate
    resp = client.post(f"/api/boards/{original_id}/duplicate", follow_redirects=False)
    dup_id = resp.json()["board"]["id"]

    # Modify duplicate
    dup_data = client.get(f"/api/boards/{dup_id}").json()["board"]
    first_card_id = dup_data["columns"][0]["cardIds"][0] if dup_data["columns"][0]["cardIds"] else None
    if first_card_id:
        dup_data["cards"][first_card_id]["title"] = "MODIFIED"
        client.put(f"/api/boards/{dup_id}", json=dup_data)

    # Original unchanged
    original_after = client.get(f"/api/boards/{original_id}").json()["board"]
    assert original_after == original_data


def test_import_export_roundtrip(tmp_path: Path) -> None:
    """Export a board's data, import it, verify the imported copy matches."""
    client = make_test_client(tmp_path)
    login_test_client(client)

    # Get existing board data
    boards = client.get("/api/boards").json()["boards"]
    original_id = boards[0]["id"]
    original = client.get(f"/api/boards/{original_id}").json()

    # Import the board data as a new board
    resp = client.post("/api/boards/import", json={
        "title": "Imported Copy",
        "description": original["description"],
        "board": original["board"],
    })
    assert resp.status_code == 201
    imported_id = resp.json()["board"]["id"]

    # Fetch imported board data and compare structure
    imported = client.get(f"/api/boards/{imported_id}").json()
    assert len(imported["board"]["columns"]) == len(original["board"]["columns"])
    assert len(imported["board"]["cards"]) == len(original["board"]["cards"])


def test_dashboard_stats_reflect_mutations(tmp_path: Path) -> None:
    """Stats update after creating/archiving boards."""
    client = make_test_client(tmp_path)
    login_test_client(client)

    initial_stats = client.get("/api/dashboard/stats").json()

    # Create a board
    client.post("/api/boards", json={"title": "Extra"})
    after_create = client.get("/api/dashboard/stats").json()
    assert after_create["total_boards"] == initial_stats["total_boards"] + 1

    # Archive the new board
    boards = client.get("/api/boards").json()["boards"]
    new_board = next(b for b in boards if b["title"] == "Extra")
    client.post(f"/api/boards/{new_board['id']}/archive")

    after_archive = client.get("/api/dashboard/stats").json()
    assert after_archive["total_boards"] == initial_stats["total_boards"]


def test_board_stats_accuracy(tmp_path: Path) -> None:
    """Board-level stats correctly reflect card priorities and columns."""
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards", json={"title": "Stats Test"})
    board_id = resp.json()["board"]["id"]

    board_data = {
        "columns": [
            {"id": "col-1", "title": "Todo", "cardIds": ["card-1", "card-2"]},
            {"id": "col-2", "title": "Done", "cardIds": ["card-3"]},
        ],
        "cards": {
            "card-1": {"id": "card-1", "title": "A", "details": "", "priority": "high"},
            "card-2": {"id": "card-2", "title": "B", "details": "", "priority": "low"},
            "card-3": {"id": "card-3", "title": "C", "details": "", "priority": "high", "due_date": "2020-01-01"},
        },
    }
    client.put(f"/api/boards/{board_id}", json=board_data)

    stats = client.get(f"/api/boards/{board_id}/stats").json()
    assert stats["total_cards"] == 3
    assert stats["total_columns"] == 2
    assert stats["by_priority"]["high"] == 2
    assert stats["by_priority"]["low"] == 1
    assert stats["overdue_count"] == 1
    assert stats["cards_per_column"][0]["count"] == 2
    assert stats["cards_per_column"][1]["count"] == 1


def test_user_profile_update_persists(tmp_path: Path) -> None:
    """Update display name and verify it persists across requests."""
    client = make_test_client(tmp_path)
    login_test_client(client)

    client.patch("/api/me", json={"display_name": "Alice"})
    me = client.get("/api/me").json()
    assert me["display_name"] == "Alice"

    # Update again
    client.patch("/api/me", json={"display_name": "Bob"})
    me = client.get("/api/me").json()
    assert me["display_name"] == "Bob"
