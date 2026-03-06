import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.ai_client import (
    MissingApiKeyError,
    OpenAIChatError,
    OpenAIConnectivityError,
    get_openai_model,
    run_connectivity_check,
    run_structured_chat,
)


class _FakeOpenAIClient:
    def __init__(self, *, output_text: str = "4", should_raise: Exception | None = None):
        self._output_text = output_text
        self._should_raise = should_raise
        self.responses = self

    def create(self, **_kwargs):
        if self._should_raise is not None:
            raise self._should_raise
        return type("Response", (), {"output_text": self._output_text})()


def test_missing_api_key_raises() -> None:
    with pytest.raises(MissingApiKeyError):
        run_connectivity_check(api_key=None, client_factory=lambda **_: _FakeOpenAIClient())


def test_connectivity_success_returns_output_text() -> None:
    output = run_connectivity_check(
        api_key="test-key",
        client_factory=lambda **_: _FakeOpenAIClient(output_text="4"),
    )

    assert output == "4"


def test_connectivity_error_is_wrapped() -> None:
    with pytest.raises(OpenAIConnectivityError):
        run_connectivity_check(
            api_key="test-key",
            client_factory=lambda **_: _FakeOpenAIClient(should_raise=RuntimeError("boom")),
        )


def test_empty_output_is_rejected() -> None:
    with pytest.raises(OpenAIConnectivityError):
        run_connectivity_check(
            api_key="test-key",
            client_factory=lambda **_: _FakeOpenAIClient(output_text=""),
        )


def test_structured_chat_success_returns_parsed_json() -> None:
    output = run_structured_chat(
        api_key="test-key",
        board={"columns": [], "cards": {}},
        user_prompt="Create something",
        conversation_history=[],
        client_factory=lambda **_: _FakeOpenAIClient(
            output_text='{"assistant_message":"Done","board_update":null}'
        ),
    )

    assert output["assistant_message"] == "Done"
    assert output["board_update"] is None


def test_structured_chat_empty_output_is_rejected() -> None:
    with pytest.raises(OpenAIChatError):
        run_structured_chat(
            api_key="test-key",
            board={"columns": [], "cards": {}},
            user_prompt="Create something",
            conversation_history=[],
            client_factory=lambda **_: _FakeOpenAIClient(output_text=""),
        )


def test_structured_chat_error_is_wrapped() -> None:
    with pytest.raises(OpenAIChatError):
        run_structured_chat(
            api_key="test-key",
            board={"columns": [], "cards": {}},
            user_prompt="Create something",
            conversation_history=[],
            client_factory=lambda **_: _FakeOpenAIClient(should_raise=RuntimeError("boom")),
        )


def test_openai_model_defaults_to_mini(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_MODEL", raising=False)

    assert get_openai_model() == "gpt-4.1-mini"


def test_openai_model_can_be_overridden(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4.1-nano")

    assert get_openai_model() == "gpt-4.1-nano"
