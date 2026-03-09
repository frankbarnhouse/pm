from pathlib import Path

from conftest import make_test_client, login_test_client
from app import ai_client
from app.routes import api as api_routes


def test_connectivity_requires_authentication(tmp_path: Path) -> None:
    client = make_test_client(tmp_path)

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 401


def test_connectivity_returns_expected_shape(tmp_path: Path, monkeypatch) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    monkeypatch.setattr(api_routes, "run_connectivity_check", lambda: "4")

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["model"] == ai_client.get_openai_model()
    assert payload["prompt"] == "2+2"
    assert payload["response"] == "4"


def test_connectivity_missing_key_returns_503(tmp_path: Path, monkeypatch) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    monkeypatch.setattr(
        api_routes,
        "run_connectivity_check",
        lambda: (_ for _ in ()).throw(ai_client.MissingApiKeyError("OPENAI_API_KEY is not configured")),
    )

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 503
    assert "OPENAI_API_KEY" in response.json()["detail"]


def test_connectivity_provider_failure_returns_502(tmp_path: Path, monkeypatch) -> None:
    client = make_test_client(tmp_path)
    login_test_client(client)

    monkeypatch.setattr(
        api_routes,
        "run_connectivity_check",
        lambda: (_ for _ in ()).throw(ai_client.OpenAIConnectivityError("401 unauthorized")),
    )

    response = client.post("/api/ai/connectivity")

    assert response.status_code == 502
    assert "OpenAI connectivity failed" in response.json()["detail"]
