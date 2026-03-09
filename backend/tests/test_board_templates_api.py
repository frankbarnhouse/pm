from pathlib import Path

from conftest import make_test_client, login_test_client


def test_list_templates_requires_auth(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    response = client.get("/api/boards/templates")
    assert response.status_code == 401


def test_list_templates_returns_all(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    response = client.get("/api/boards/templates")
    assert response.status_code == 200
    templates = response.json()["templates"]
    ids = [t["id"] for t in templates]
    assert "blank" in ids
    assert "scrum" in ids
    assert "bug_tracking" in ids
    assert "product_launch" in ids


def test_templates_have_descriptions(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    templates = client.get("/api/boards/templates").json()["templates"]
    for t in templates:
        assert t["description"] != ""
        assert t["column_count"] > 0
        assert t["name"] != ""


def test_create_board_with_blank_template(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards", json={"title": "Blank Board", "template": "blank"})
    assert resp.status_code == 201
    board_id = resp.json()["board"]["id"]

    board = client.get(f"/api/boards/{board_id}").json()["board"]
    col_titles = [c["title"] for c in board["columns"]]
    assert "Backlog" in col_titles
    assert "Done" in col_titles


def test_create_board_with_scrum_template(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards", json={"title": "Sprint Board", "template": "scrum"})
    board_id = resp.json()["board"]["id"]

    board = client.get(f"/api/boards/{board_id}").json()["board"]
    col_titles = [c["title"] for c in board["columns"]]
    assert "Product Backlog" in col_titles
    assert "Sprint Backlog" in col_titles
    assert "Testing" in col_titles
    assert len(board["columns"]) == 6


def test_create_board_with_bug_tracking_template(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards", json={"title": "Bugs", "template": "bug_tracking"})
    board_id = resp.json()["board"]["id"]

    board = client.get(f"/api/boards/{board_id}").json()["board"]
    col_titles = [c["title"] for c in board["columns"]]
    assert "Reported" in col_titles
    assert "Confirmed" in col_titles
    assert "Closed" in col_titles


def test_create_board_with_product_launch_template(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards", json={"title": "Launch Plan", "template": "product_launch"})
    board_id = resp.json()["board"]["id"]

    board = client.get(f"/api/boards/{board_id}").json()["board"]
    col_titles = [c["title"] for c in board["columns"]]
    assert "Ideas" in col_titles
    assert "Launch" in col_titles
    assert "Post-Launch" in col_titles
    assert len(board["columns"]) == 6


def test_create_board_invalid_template_rejected(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards", json={"title": "Bad", "template": "nonexistent"})
    assert resp.status_code == 422


def test_default_template_is_blank(tmp_path: Path) -> None:
    """When no template is specified, blank is used."""
    client = make_test_client(tmp_path)
    login_test_client(client)

    resp = client.post("/api/boards", json={"title": "Default"})
    board_id = resp.json()["board"]["id"]

    board = client.get(f"/api/boards/{board_id}").json()["board"]
    assert len(board["columns"]) == 4  # blank template has 4 columns
