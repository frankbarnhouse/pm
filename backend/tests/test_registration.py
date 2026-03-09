from pathlib import Path

from conftest import make_test_client
from app.database import get_user_by_username, username_exists, verify_credentials
from app.session import SESSION_COOKIE


def test_register_page_renders_form(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.get("/register")

    assert response.status_code == 200
    assert "Create account" in response.text
    assert 'name="username"' in response.text
    assert 'name="password"' in response.text
    assert 'name="display_name"' in response.text


def test_register_success_creates_user_and_logs_in(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.post(
        "/auth/register",
        data={"username": "alice", "password": "secret123", "display_name": "Alice"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert SESSION_COOKIE in response.cookies

    assert verify_credentials("alice", "secret123")
    user = get_user_by_username("alice")
    assert user is not None
    assert user["display_name"] == "Alice"


def test_register_creates_default_board(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    client.post(
        "/auth/register",
        data={"username": "bob", "password": "pass1234"},
        follow_redirects=False,
    )

    # Login as the new user and check boards
    response = client.get("/api/boards")
    assert response.status_code == 200
    boards = response.json()["boards"]
    assert len(boards) == 1
    assert boards[0]["title"] == "My First Board"


def test_register_duplicate_username_shows_error(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    # "user" already exists from MVP seed
    response = client.post(
        "/auth/register",
        data={"username": "user", "password": "newpassword"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "error=1" in response.headers["location"]


def test_register_short_username_shows_error(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.post(
        "/auth/register",
        data={"username": "ab", "password": "password"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "error=2" in response.headers["location"]


def test_register_invalid_username_chars_shows_error(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.post(
        "/auth/register",
        data={"username": "user@name", "password": "password"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "error=2" in response.headers["location"]


def test_register_short_password_shows_error(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.post(
        "/auth/register",
        data={"username": "validuser", "password": "abc"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert "error=3" in response.headers["location"]


def test_register_page_redirects_when_logged_in(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    # Login first
    client.post(
        "/auth/login",
        data={"username": "user", "password": "password"},
        follow_redirects=False,
    )

    response = client.get("/register", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/"


def test_username_exists_function(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    assert username_exists("user") is True
    assert username_exists("nonexistent") is False


def test_register_with_hyphen_underscore_username(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.post(
        "/auth/register",
        data={"username": "my-user_name", "password": "password"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert verify_credentials("my-user_name", "password")
