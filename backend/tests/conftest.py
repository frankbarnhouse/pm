from pathlib import Path
from fastapi.testclient import TestClient
from app import main
from app.database import DB_PATH as _unused_db_path, initialize_database
from app.routes.frontend import FRONTEND_DIST_DIR as _unused_frontend_dir
from app.session import SESSION_STORE, SESSION_CHAT_HISTORY
import app.database
import app.routes.frontend


def make_test_client(tmp_path: Path) -> TestClient:
    dist_dir = tmp_path / "frontend_dist"
    dist_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text("<html><body>Kanban Studio</body></html>")
    db_path = tmp_path / "data" / "app.db"
    app.routes.frontend.FRONTEND_DIST_DIR = dist_dir
    app.database.DB_PATH = db_path
    SESSION_STORE.clear()
    SESSION_CHAT_HISTORY.clear()
    initialize_database()
    return TestClient(main.app)


def login_test_client(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        data={"username": "user", "password": "password"},
        follow_redirects=False,
    )
    assert response.status_code == 303
