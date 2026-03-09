from pathlib import Path

from fastapi.testclient import TestClient

from conftest import make_test_client, login_test_client
from app import main


def test_unauthenticated_user_is_redirected_to_login(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_login_page_renders_form(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.get("/login")

    assert response.status_code == 200
    assert "Sign in" in response.text
    assert "name=\"username\"" in response.text


def test_login_failure_redirects_with_error(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.post(
        "/auth/login",
        data={"username": "user", "password": "wrong"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login?error=1"


def test_login_success_sets_cookie_and_accesses_board(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    login_response = client.post(
        "/auth/login",
        data={"username": "user", "password": "password"},
        follow_redirects=False,
    )

    assert login_response.status_code == 303
    assert login_response.headers["location"] == "/"
    assert main.SESSION_COOKIE in login_response.cookies
    assert login_response.cookies[main.SESSION_COOKIE]

    board_response = client.get("/")
    assert board_response.status_code == 200
    assert "Kanban Studio" in board_response.text


def test_logout_clears_cookie_and_blocks_board(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)
    client.post(
        "/auth/login",
        data={"username": "user", "password": "password"},
        follow_redirects=False,
    )

    logout_response = client.post("/auth/logout", follow_redirects=False)

    assert logout_response.status_code == 303
    assert logout_response.headers["location"] == "/login"

    board_response = client.get("/", follow_redirects=False)
    assert board_response.status_code == 302
    assert board_response.headers["location"] == "/login"
