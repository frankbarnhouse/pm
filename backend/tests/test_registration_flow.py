"""Tests for user registration and multi-user isolation."""

from pathlib import Path

from conftest import make_test_client


def _register_and_login(client, username: str, password: str = "testpass", display_name: str = ""):
    """Register a new user and verify auto-login."""
    data = f"username={username}&password={password}"
    if display_name:
        data += f"&display_name={display_name}"
    response = client.post(
        "/auth/register",
        content=data,
        headers={"content-type": "application/x-www-form-urlencoded"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_register_new_user(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    _register_and_login(client, "alice")

    me = client.get("/api/me").json()
    assert me["username"] == "alice"


def test_register_creates_default_board(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    _register_and_login(client, "bob")

    boards = client.get("/api/boards").json()["boards"]
    assert len(boards) == 1
    assert boards[0]["title"] == "My First Board"


def test_register_duplicate_username_rejected(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    _register_and_login(client, "charlie")

    # Logout
    client.post("/auth/logout", follow_redirects=False)

    # Try registering with same username
    response = client.post(
        "/auth/register",
        content="username=charlie&password=testpass",
        headers={"content-type": "application/x-www-form-urlencoded"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "error=1" in response.headers["location"]


def test_register_short_username_rejected(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    response = client.post(
        "/auth/register",
        content="username=ab&password=testpass",
        headers={"content-type": "application/x-www-form-urlencoded"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "error=2" in response.headers["location"]


def test_register_short_password_rejected(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    response = client.post(
        "/auth/register",
        content="username=validuser&password=abc",
        headers={"content-type": "application/x-www-form-urlencoded"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "error=3" in response.headers["location"]


def test_register_with_display_name(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    _register_and_login(client, "diana", display_name="Diana Prince")

    me = client.get("/api/me").json()
    assert me["display_name"] == "Diana Prince"


def test_multi_user_board_isolation(tmp_path: Path) -> None:
    """Two users cannot see each other's boards."""
    client = make_test_client(tmp_path)

    # Register user A and create a board
    _register_and_login(client, "user_a")
    client.post("/api/boards", json={"title": "A Private Board"})
    user_a_boards = client.get("/api/boards").json()["boards"]
    assert any(b["title"] == "A Private Board" for b in user_a_boards)

    # Logout
    client.post("/auth/logout", follow_redirects=False)

    # Register user B
    _register_and_login(client, "user_b")
    user_b_boards = client.get("/api/boards").json()["boards"]
    assert not any(b["title"] == "A Private Board" for b in user_b_boards)


def test_login_after_registration(tmp_path: Path) -> None:
    """After registering, logging out, and logging back in works."""
    client = make_test_client(tmp_path)
    _register_and_login(client, "eve", password="secure123")

    # Logout
    client.post("/auth/logout", follow_redirects=False)

    # Verify logged out
    me_resp = client.get("/api/me")
    assert me_resp.status_code == 401

    # Login with registered credentials
    response = client.post(
        "/auth/login",
        content="username=eve&password=secure123",
        headers={"content-type": "application/x-www-form-urlencoded"},
        follow_redirects=False,
    )
    assert response.status_code == 303

    me = client.get("/api/me").json()
    assert me["username"] == "eve"
