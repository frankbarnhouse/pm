import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import ai_client, main


def _make_client(tmp_path: Path) -> TestClient:
    dist_dir = tmp_path / "frontend_dist"
    dist_dir.mkdir(parents=True)
    (dist_dir / "index.html").write_text("<html><body>Kanban Studio</body></html>")

    db_path = tmp_path / "data" / "app.db"
    main.FRONTEND_DIST_DIR = dist_dir
    main.DB_PATH = db_path
    main._initialize_database()

    return TestClient(main.app)


def _login(client: TestClient) -> None:
    response = client.post(
        "/auth/login",
        data={"username": "user", "password": "password"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_connectivity_requires_authentication(tmp_path: Path) -> None:
    client = _make_client(tmp_path)

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 401


def test_connectivity_returns_expected_shape(tmp_path: Path, monkeypatch) -> None:
    client = _make_client(tmp_path)
    _login(client)

    monkeypatch.setattr(main, "run_connectivity_check", lambda: "4")

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["model"] == ai_client.get_openai_model()
    assert payload["prompt"] == "2+2"
    assert payload["response"] == "4"


def test_connectivity_missing_key_returns_503(tmp_path: Path, monkeypatch) -> None:
    client = _make_client(tmp_path)
    _login(client)

    monkeypatch.setattr(
        main,
        "run_connectivity_check",
        lambda: (_ for _ in ()).throw(ai_client.MissingApiKeyError("OPENAI_API_KEY is not configured")),
    )

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_connectivity_provider_failure_returns_502(tmp_path: Path, monkeypatch) -> None:
    client = _make_client(tmp_path)
    _login(client)

    monkeypatch.setattr(
        main,
        "run_connectivity_check",
        lambda: (_ for _ in ()).throw(ai_client.OpenAIConnectivityError("401 unauthorized")),
    )

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 502
    assert "OpenAI connectivity failed" in response.json()["detail"]
