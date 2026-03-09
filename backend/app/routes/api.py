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
    archive_board,
    change_user_password,
    create_board,
    delete_board,
    duplicate_board,
    get_board,
    get_board_activity,
    hash_password,
    list_user_boards_with_counts,
    log_activity,
    read_board_data,
    read_user_board,
    update_board_meta,
    update_user_display_name,
    write_board_data,
    write_user_board,
)
from app.models import (
    AddChecklistItemOperation,
    AddChecklistItemRequest,
    AddCommentOperation,
    AddCommentRequest,
    AIChatResultPayload,
    ClearColumnOperation,
    DeleteChecklistItemOperation,
    BoardPayload,
    ChangePasswordRequest,
    ChatMessagePayload,
    CreateBoardRequest,
    DeleteCommentOperation,
    ImportBoardRequest,
    SetWipLimitOperation,
    ToggleChecklistItemOperation,
    UpdateBoardMetaRequest,
    UpdateProfileRequest,
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


@router.patch("/me")
def update_profile(request: Request, payload: UpdateProfileRequest) -> dict:
    user = require_api_user(request)
    if payload.display_name is not None:
        update_user_display_name(user["id"], payload.display_name)
    from app.database import get_user_by_username

    updated = get_user_by_username(user["username"])
    return {
        "id": updated["id"],
        "username": updated["username"],
        "display_name": updated["display_name"],
    }


@router.post("/me/password")
def change_password(request: Request, payload: ChangePasswordRequest) -> dict:
    user = require_api_user(request)
    expected_hash = hash_password(payload.current_password, user["password_salt"])
    if user["password_hash"] != expected_hash:
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    change_user_password(user["id"], payload.new_password)
    return {"changed": True}


# --- Multi-board endpoints ---


@router.get("/dashboard/stats")
def get_dashboard_stats(request: Request) -> dict:
    user = require_api_user(request)
    boards = list_user_boards_with_counts(user["id"])
    total_boards = len(boards)
    total_cards = sum(b["card_count"] for b in boards)
    total_columns = sum(b["column_count"] for b in boards)
    return {
        "total_boards": total_boards,
        "total_cards": total_cards,
        "total_columns": total_columns,
    }


@router.post("/boards/import", status_code=201)
def import_board(request: Request, payload: ImportBoardRequest) -> dict:
    user = require_api_user(request)
    # Validate board structure
    try:
        BoardPayload.model_validate(payload.board)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid board data: {exc}") from exc
    board = create_board(user["id"], payload.title, payload.description, payload.board)
    return {"board": board}


@router.get("/boards")
def get_boards(request: Request, include_archived: bool = False) -> dict:
    user = require_api_user(request)
    boards = list_user_boards_with_counts(user["id"], include_archived=include_archived)
    return {"boards": boards}


@router.get("/boards/templates")
def get_board_templates(request: Request) -> dict:
    require_api_user(request)
    from app.database import BOARD_TEMPLATE_DATA
    templates = []
    descriptions = {
        "blank": "Basic kanban board with Backlog, In Progress, Review, and Done columns.",
        "scrum": "Scrum-style board with Product Backlog, Sprint Backlog, In Progress, Review, Testing, and Done.",
        "bug_tracking": "Bug tracking workflow: Reported, Confirmed, Fixing, Testing, Closed.",
        "product_launch": "Product launch pipeline: Ideas, Research, Design, Development, Launch, Post-Launch.",
    }
    for key in BOARD_TEMPLATE_DATA:
        templates.append({
            "id": key,
            "name": key.replace("_", " ").title(),
            "description": descriptions.get(key, ""),
            "column_count": len(BOARD_TEMPLATE_DATA[key]["columns"]),
        })
    return {"templates": templates}


@router.post("/boards", status_code=201)
def create_new_board(request: Request, payload: CreateBoardRequest) -> dict:
    user = require_api_user(request)
    board = create_board(user["id"], payload.title, payload.description, template=payload.template)
    log_activity(board["id"], user["id"], "board_created", f"Created board '{payload.title}'")
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
    log_activity(board_id, user["id"], "board_updated", "Board data saved")
    return {"board": board}


@router.patch("/boards/{board_id}")
def patch_board_meta(request: Request, board_id: int, payload: UpdateBoardMetaRequest) -> dict:
    user = require_api_user(request)
    updated = update_board_meta(board_id, user["id"], payload.title, payload.description)
    return {"board": updated}


@router.post("/boards/{board_id}/archive")
def archive_board_endpoint(request: Request, board_id: int) -> dict:
    user = require_api_user(request)
    if not archive_board(board_id, user["id"], archived=True):
        raise HTTPException(status_code=404, detail="Board not found")
    return {"archived": True}


@router.post("/boards/{board_id}/unarchive")
def unarchive_board_endpoint(request: Request, board_id: int) -> dict:
    user = require_api_user(request)
    if not archive_board(board_id, user["id"], archived=False):
        raise HTTPException(status_code=404, detail="Board not found")
    return {"archived": False}


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


@router.get("/boards/{board_id}/stats")
def get_board_stats(request: Request, board_id: int) -> dict:
    user = require_api_user(request)
    board = read_board_data(board_id, user["id"])
    cards = board.get("cards", {})
    columns = board.get("columns", [])

    total_cards = len(cards)
    by_priority = {"high": 0, "medium": 0, "low": 0, "none": 0}
    overdue_count = 0
    from datetime import date

    today = date.today().isoformat()
    for card in cards.values():
        p = card.get("priority")
        if p in by_priority:
            by_priority[p] += 1
        else:
            by_priority["none"] += 1
        due = card.get("due_date")
        if due and due < today:
            overdue_count += 1

    cards_per_column = [
        {"column_id": col["id"], "title": col["title"], "count": len(col.get("cardIds", []))}
        for col in columns
    ]

    return {
        "total_cards": total_cards,
        "total_columns": len(columns),
        "by_priority": by_priority,
        "overdue_count": overdue_count,
        "cards_per_column": cards_per_column,
    }


@router.get("/boards/{board_id}/activity")
def get_activity(request: Request, board_id: int) -> dict:
    user = require_api_user(request)
    entries = get_board_activity(board_id, user["id"])
    return {"activity": entries}


@router.post("/boards/{board_id}/cards/{card_id}/comments", status_code=201)
def add_comment(request: Request, board_id: int, card_id: str, payload: AddCommentRequest) -> dict:
    user = require_api_user(request)
    board = read_board_data(board_id, user["id"])
    display_name = user["display_name"] or user["username"]
    updated = apply_board_operations(board, [
        AddCommentOperation(type="add_comment", card_id=card_id, text=payload.text, author=display_name),
    ])
    write_board_data(board_id, user["id"], updated)
    log_activity(board_id, user["id"], "comment_added", f"Comment on {card_id}")
    card = updated["cards"][card_id]
    return {"comment": card["comments"][-1]}


@router.delete("/boards/{board_id}/cards/{card_id}/comments/{comment_id}")
def delete_comment(request: Request, board_id: int, card_id: str, comment_id: str) -> dict:
    user = require_api_user(request)
    board = read_board_data(board_id, user["id"])
    try:
        updated = apply_board_operations(board, [
            DeleteCommentOperation(type="delete_comment", card_id=card_id, comment_id=comment_id),
        ])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    write_board_data(board_id, user["id"], updated)
    return {"deleted": True}


@router.post("/boards/{board_id}/cards/{card_id}/checklist", status_code=201)
def add_checklist_item(request: Request, board_id: int, card_id: str, payload: AddChecklistItemRequest) -> dict:
    user = require_api_user(request)
    board = read_board_data(board_id, user["id"])
    updated = apply_board_operations(board, [
        AddChecklistItemOperation(type="add_checklist_item", card_id=card_id, text=payload.text),
    ])
    write_board_data(board_id, user["id"], updated)
    card = updated["cards"][card_id]
    return {"item": card["checklist"][-1]}


@router.post("/boards/{board_id}/cards/{card_id}/checklist/{item_id}/toggle")
def toggle_checklist_item(request: Request, board_id: int, card_id: str, item_id: str) -> dict:
    user = require_api_user(request)
    board = read_board_data(board_id, user["id"])
    try:
        updated = apply_board_operations(board, [
            ToggleChecklistItemOperation(type="toggle_checklist_item", card_id=card_id, item_id=item_id),
        ])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    write_board_data(board_id, user["id"], updated)
    item = next(i for i in updated["cards"][card_id]["checklist"] if i["id"] == item_id)
    return {"item": item}


@router.delete("/boards/{board_id}/cards/{card_id}/checklist/{item_id}")
def delete_checklist_item(request: Request, board_id: int, card_id: str, item_id: str) -> dict:
    user = require_api_user(request)
    board = read_board_data(board_id, user["id"])
    try:
        updated = apply_board_operations(board, [
            DeleteChecklistItemOperation(type="delete_checklist_item", card_id=card_id, item_id=item_id),
        ])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    write_board_data(board_id, user["id"], updated)
    return {"deleted": True}


@router.post("/boards/{board_id}/columns/{column_id}/wip-limit")
def set_wip_limit(request: Request, board_id: int, column_id: str, payload: dict) -> dict:
    user = require_api_user(request)
    board = read_board_data(board_id, user["id"])
    wip_limit = payload.get("wip_limit")
    try:
        updated = apply_board_operations(board, [
            SetWipLimitOperation(type="set_wip_limit", column_id=column_id, wip_limit=wip_limit),
        ])
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    write_board_data(board_id, user["id"], updated)
    return {"wip_limit": wip_limit}


@router.post("/boards/{board_id}/columns/{column_id}/clear")
def clear_column(request: Request, board_id: int, column_id: str) -> dict:
    user = require_api_user(request)
    board = read_board_data(board_id, user["id"])
    try:
        updated = apply_board_operations(board, [
            ClearColumnOperation(type="clear_column", column_id=column_id),
        ])
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    write_board_data(board_id, user["id"], updated)
    log_activity(board_id, user["id"], "column_cleared", f"Cleared column {column_id}")
    return {"cleared": True}


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
            op_types = ", ".join(op.type for op in result.board_update.operations)
            log_activity(board_id, user["id"], "ai_update", f"AI applied: {op_types}")
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
