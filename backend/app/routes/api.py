import json
import logging

from fastapi import APIRouter, HTTPException, Request

from app.ai_client import (
    get_openai_model,
    MissingApiKeyError,
    OpenAIChatError,
    OpenAIConnectivityError,
    run_connectivity_check,
    run_structured_chat,
)
from app.board_ops import apply_board_operations
from app.database import (
    create_board,
    delete_board,
    duplicate_board,
    get_board,
    list_user_boards_with_counts,
    read_board_data,
    read_user_board,
    update_board_meta,
    write_board_data,
    write_user_board,
)
from app.models import (
    AIChatResultPayload,
    BoardPayload,
    ChatMessagePayload,
    CreateBoardRequest,
    UpdateBoardMetaRequest,
)
from app.session import (
    MAX_CHAT_HISTORY_MESSAGES,
    get_session_history,
    require_api_user,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


@router.get("/me")
def get_current_user(request: Request) -> dict:
    user = require_api_user(request)
    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
    }


# --- Multi-board endpoints ---


@router.get("/boards")
def get_boards(request: Request) -> dict:
    user = require_api_user(request)
    boards = list_user_boards_with_counts(user["id"])
    return {"boards": boards}


@router.post("/boards", status_code=201)
def create_new_board(request: Request, payload: CreateBoardRequest) -> dict:
    user = require_api_user(request)
    board = create_board(user["id"], payload.title, payload.description)
    return {"board": board}


@router.get("/boards/{board_id}")
def get_board_by_id(request: Request, board_id: int) -> dict:
    user = require_api_user(request)
    board_row = get_board(board_id, user["id"])
    board_data = json.loads(board_row["board_json"])
    return {
        "id": board_row["id"],
        "title": board_row["title"],
        "description": board_row["description"],
        "board": board_data,
    }


@router.put("/boards/{board_id}")
def put_board_by_id(request: Request, board_id: int, payload: BoardPayload) -> dict:
    user = require_api_user(request)
    board = payload.model_dump()
    write_board_data(board_id, user["id"], board)
    return {"board": board}


@router.patch("/boards/{board_id}")
def patch_board_meta(request: Request, board_id: int, payload: UpdateBoardMetaRequest) -> dict:
    user = require_api_user(request)
    updated = update_board_meta(board_id, user["id"], payload.title, payload.description)
    return {"board": updated}


@router.post("/boards/{board_id}/duplicate", status_code=201)
def duplicate_board_endpoint(request: Request, board_id: int) -> dict:
    user = require_api_user(request)
    board = duplicate_board(board_id, user["id"])
    return {"board": board}


@router.delete("/boards/{board_id}")
def delete_board_by_id(request: Request, board_id: int) -> dict:
    user = require_api_user(request)
    deleted = delete_board(board_id, user["id"])
    if not deleted:
        raise HTTPException(status_code=404, detail="Board not found")
    return {"deleted": True}


@router.post("/boards/{board_id}/chat")
def board_chat(request: Request, board_id: int, payload: ChatMessagePayload) -> dict[str, str | bool | None]:
    user = require_api_user(request)
    board = read_board_data(board_id, user["id"])
    history = get_session_history(request)

    try:
        raw_result = run_structured_chat(
            board=board,
            user_prompt=payload.prompt,
            conversation_history=history,
        )
        result = AIChatResultPayload.model_validate(raw_result)
    except MissingApiKeyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OpenAIChatError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI chat failed: {exc}") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Invalid AI structured response: {exc}") from exc

    board_updated = False
    update_error = None
    if result.board_update is not None:
        try:
            updated_board = apply_board_operations(board, result.board_update.operations)
            write_board_data(board_id, user["id"], updated_board)
            board_updated = True
        except ValueError as exc:
            board_updated = False
            update_error = str(exc)
            logger.error("Board operation failed: %s", update_error)

    history.append({"role": "user", "content": payload.prompt})
    history.append({"role": "assistant", "content": result.assistant_message})
    history[:] = history[-MAX_CHAT_HISTORY_MESSAGES:]

    return {
        "assistant_message": result.assistant_message,
        "board_updated": board_updated,
        "update_error": update_error,
    }


# --- Legacy single-board endpoints (backwards compatible) ---


@router.get("/board")
def get_board_legacy(request: Request) -> dict:
    user = require_api_user(request)
    return {"board": read_user_board(user["id"])}


@router.put("/board")
def put_board_legacy(request: Request, payload: BoardPayload) -> dict:
    user = require_api_user(request)
    board = payload.model_dump()
    write_user_board(user["id"], board)
    return {"board": board}


@router.post("/ai/connectivity")
def ai_connectivity(request: Request) -> dict[str, str | bool]:
    require_api_user(request)

    try:
        response_text = run_connectivity_check()
    except MissingApiKeyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OpenAIConnectivityError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI connectivity failed: {exc}") from exc

    return {
        "ok": True,
        "model": get_openai_model(),
        "prompt": "2+2",
        "response": response_text,
    }


@router.post("/chat")
def chat(request: Request, payload: ChatMessagePayload) -> dict[str, str | bool | None]:
    user = require_api_user(request)
    board = read_user_board(user["id"])
    history = get_session_history(request)

    try:
        raw_result = run_structured_chat(
            board=board,
            user_prompt=payload.prompt,
            conversation_history=history,
        )
        result = AIChatResultPayload.model_validate(raw_result)
    except MissingApiKeyError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except OpenAIChatError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI chat failed: {exc}") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise HTTPException(status_code=502, detail=f"Invalid AI structured response: {exc}") from exc

    board_updated = False
    update_error = None
    if result.board_update is not None:
        try:
            updated_board = apply_board_operations(board, result.board_update.operations)
            write_user_board(user["id"], updated_board)
            board_updated = True
        except ValueError as exc:
            board_updated = False
            update_error = str(exc)
            logger.error("Board operation failed: %s", update_error)

    history.append({"role": "user", "content": payload.prompt})
    history.append({"role": "assistant", "content": result.assistant_message})
    history[:] = history[-MAX_CHAT_HISTORY_MESSAGES:]

    return {
        "assistant_message": result.assistant_message,
        "board_updated": board_updated,
        "update_error": update_error,
    }
