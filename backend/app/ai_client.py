import os
import json
from typing import Any

from openai import OpenAI

OPENAI_MODEL = "gpt-4.1-mini"
OPENAI_MODEL_ENV_VAR = "OPENAI_MODEL"
CONNECTIVITY_PROMPT = "Return only the number for 2+2."

CHAT_RESPONSE_SCHEMA: dict[str, Any] = {
    "name": "kanban_chat_response",
    "schema": {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "assistant_message": {"type": "string"},
            "board_update": {
                "anyOf": [
                    {"type": "null"},
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "operations": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "type": {
                                            "type": "string",
                                            "enum": [
                                                "create_card",
                                                "edit_card",
                                                "move_card",
                                                "delete_card",
                                                "rename_column",
                                                "add_column",
                                                "delete_column",
                                            ],
                                        },
                                        "column_id": {"type": ["string", "null"]},
                                        "title": {"type": ["string", "null"]},
                                        "details": {"type": ["string", "null"]},
                                        "card_id": {"type": ["string", "null"]},
                                        "to_column_id": {"type": ["string", "null"]},
                                        "before_card_id": {"type": ["string", "null"]},
                                        "position": {"type": ["integer", "null"]},
                                    },
                                    "required": [
                                        "type",
                                        "column_id",
                                        "title",
                                        "details",
                                        "card_id",
                                        "to_column_id",
                                        "before_card_id",
                                        "position",
                                    ],
                                },
                            }
                        },
                        "required": ["operations"],
                    },
                ]
            },
        },
        "required": ["assistant_message", "board_update"],
    },
    "strict": True,
}


class MissingApiKeyError(Exception):
    pass


class OpenAIConnectivityError(Exception):
    pass


class OpenAIChatError(Exception):
    pass


def get_openai_model() -> str:
    configured_model = os.getenv(OPENAI_MODEL_ENV_VAR, OPENAI_MODEL).strip()
    return configured_model or OPENAI_MODEL


def run_connectivity_check(
    *,
    api_key: str | None = None,
    client_factory: Any = OpenAI,
) -> str:
    effective_api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not effective_api_key:
        raise MissingApiKeyError("OPENAI_API_KEY is not configured")

    try:
        client = client_factory(api_key=effective_api_key, timeout=30)
        response = client.responses.create(
            model=get_openai_model(),
            input=CONNECTIVITY_PROMPT,
        )
        output_text = (getattr(response, "output_text", "") or "").strip()
        if not output_text:
            raise OpenAIConnectivityError("OpenAI response did not include output_text")
        return output_text
    except MissingApiKeyError:
        raise
    except OpenAIConnectivityError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise OpenAIConnectivityError(str(exc)) from exc


def run_structured_chat(
    *,
    board: dict[str, Any],
    user_prompt: str,
    conversation_history: list[dict[str, str]],
    api_key: str | None = None,
    client_factory: Any = OpenAI,
) -> dict[str, Any]:
    effective_api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not effective_api_key:
        raise MissingApiKeyError("OPENAI_API_KEY is not configured")

    system_prompt = (
        "You are a project management assistant for a Kanban board. "
        "Use only the provided board context and history. "
        "When proposing updates, keep column IDs fixed to existing columns and return only valid operations."
    )

    user_payload = {
        "board": board,
        "conversation_history": conversation_history,
        "user_prompt": user_prompt,
    }

    try:
        client = client_factory(api_key=effective_api_key, timeout=30)
        response = client.responses.create(
            model=get_openai_model(),
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload)},
            ],
            text={"format": {"type": "json_schema", "name": CHAT_RESPONSE_SCHEMA["name"], "schema": CHAT_RESPONSE_SCHEMA["schema"], "strict": True}},
        )
        output_text = (getattr(response, "output_text", "") or "").strip()
        if not output_text:
            raise OpenAIChatError("OpenAI response did not include output_text")
        return json.loads(output_text)
    except MissingApiKeyError:
        raise
    except OpenAIChatError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise OpenAIChatError(str(exc)) from exc
