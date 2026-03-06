import os
from typing import Any

from openai import OpenAI

OPENAI_MODEL = "gpt-4.1-mini"
CONNECTIVITY_PROMPT = "Return only the number for 2+2."


class MissingApiKeyError(Exception):
    pass


class OpenAIConnectivityError(Exception):
    pass


def run_connectivity_check(
    *,
    api_key: str | None = None,
    client_factory: Any = OpenAI,
) -> str:
    effective_api_key = api_key or os.getenv("OPENAI_API_KEY")
    if not effective_api_key:
        raise MissingApiKeyError("OPENAI_API_KEY is not configured")

    try:
        client = client_factory(api_key=effective_api_key)
        response = client.responses.create(
            model=OPENAI_MODEL,
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
