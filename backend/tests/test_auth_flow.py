import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import main


def _make_client_with_frontend(tmp_path: Path) -> TestClient:
    dist_dir = tmp_path / "frontend_dist"
    dist_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text("<html><body>Kanban Studio</body></html>")

    db_path = tmp_path / "data" / "app.db"
    main.FRONTEND_DIST_DIR = dist_dir
    main.DB_PATH = db_path
    main._initialize_database()

    return TestClient(main.app)


def test_unauthenticated_user_is_redirected_to_login(tmp_path: Path) -> None:
    client = _make_client_with_frontend(tmp_path)

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_login_page_renders_form(tmp_path: Path) -> None:
    client = _make_client_with_frontend(tmp_path)

    response = client.get("/login")

    assert response.status_code == 200
    assert "Sign in" in response.text
    assert "name=\"username\"" in response.text


def test_login_failure_redirects_with_error(tmp_path: Path) -> None:
    client = _make_client_with_frontend(tmp_path)

    response = client.post(
        "/auth/login",
        data={"username": "user", "password": "wrong"},
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/login?error=1"


def test_login_success_sets_cookie_and_accesses_board(tmp_path: Path) -> None:
    client = _make_client_with_frontend(tmp_path)

    login_response = client.post(
        "/auth/login",
        data={"username": "user", "password": "password"},
        follow_redirects=False,
    )

    assert login_response.status_code == 303
    assert login_response.headers["location"] == "/"
    assert main.SESSION_COOKIE in login_response.cookies
    assert main.SESSION_ID_COOKIE in login_response.cookies
    assert login_response.cookies[main.SESSION_COOKIE] == main.MVP_USERNAME

    board_response = client.get("/")
    assert board_response.status_code == 200
    assert "Kanban Studio" in board_response.text


def test_logout_clears_cookie_and_blocks_board(tmp_path: Path) -> None:
    client = _make_client_with_frontend(tmp_path)
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
