from pathlib import Path
from fastapi.testclient import TestClient
from app import main


def make_test_client(tmp_path: Path) -> TestClient:
    dist_dir = tmp_path / "frontend_dist"
    dist_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text("<html><body>Kanban Studio</body></html>")
    db_path = tmp_path / "data" / "app.db"
    main.FRONTEND_DIST_DIR = dist_dir
    main.DB_PATH = db_path
    main.SESSION_STORE.clear()
    main.SESSION_CHAT_HISTORY.clear()
    main._initialize_database()
    return TestClient(main.app)


def login_test_client(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        data={"username": "user", "password": "password"},
        follow_redirects=False,
    )
    assert response.status_code == 303
