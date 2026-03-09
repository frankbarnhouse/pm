from copy import deepcopy
from datetime import datetime, timezone

from app.models import BoardOperation, BoardPayload


def _next_card_id(board: dict) -> str:
    max_suffix = 0
    for card_id in board["cards"].keys():
        if not card_id.startswith("card-"):
            continue
        suffix = card_id.removeprefix("card-")
        if suffix.isdigit():
            max_suffix = max(max_suffix, int(suffix))
    return f"card-{max_suffix + 1}"


def _next_column_id(board: dict) -> str:
    max_suffix = 0
    for column in board["columns"]:
        col_id = column["id"]
        if not col_id.startswith("col-"):
            continue
        suffix = col_id.removeprefix("col-")
        if suffix.isdigit():
            max_suffix = max(max_suffix, int(suffix))
    return f"col-{max_suffix + 1}"


def _find_column(board: dict, column_id: str) -> dict:
    for column in board["columns"]:
        if column["id"] == column_id:
            return column
    raise ValueError(f"Unknown column_id: {column_id}")


def _remove_card_from_columns(board: dict, card_id: str) -> None:
    for column in board["columns"]:
        if card_id in column["cardIds"]:
            column["cardIds"] = [existing_id for existing_id in column["cardIds"] if existing_id != card_id]


def apply_board_operations(current_board: dict, operations: list[BoardOperation]) -> dict:
    board = deepcopy(current_board)

    for operation in operations:
        if operation.type == "create_card":
            column = _find_column(board, operation.column_id)
            new_card_id = _next_card_id(board)
            board["cards"][new_card_id] = {
                "id": new_card_id,
                "title": operation.title,
                "details": operation.details,
            }
            column["cardIds"].append(new_card_id)
            continue

        if operation.type == "edit_card":
            card = board["cards"].get(operation.card_id)
            if card is None:
                raise ValueError(f"Unknown card_id: {operation.card_id}")
            if operation.title is not None:
                card["title"] = operation.title
            if operation.details is not None:
                card["details"] = operation.details
            continue

        if operation.type == "move_card":
            if operation.card_id not in board["cards"]:
                raise ValueError(f"Unknown card_id: {operation.card_id}")

            destination = _find_column(board, operation.to_column_id)
            _remove_card_from_columns(board, operation.card_id)

            if operation.before_card_id is None:
                destination["cardIds"].append(operation.card_id)
                continue

            if operation.before_card_id not in destination["cardIds"]:
                raise ValueError(f"before_card_id must be in destination column: {operation.before_card_id}")

            insert_index = destination["cardIds"].index(operation.before_card_id)
            destination["cardIds"].insert(insert_index, operation.card_id)
            continue

        if operation.type == "delete_card":
            if operation.card_id not in board["cards"]:
                raise ValueError(f"Unknown card_id: {operation.card_id}")
            _remove_card_from_columns(board, operation.card_id)
            del board["cards"][operation.card_id]
            continue

        if operation.type == "rename_column":
            column = _find_column(board, operation.column_id)
            column["title"] = operation.title
            continue

        if operation.type == "add_column":
            new_col_id = _next_column_id(board)
            new_column = {
                "id": new_col_id,
                "title": operation.title,
                "cardIds": [],
            }
            if operation.position is not None and 0 <= operation.position <= len(board["columns"]):
                board["columns"].insert(operation.position, new_column)
            else:
                board["columns"].append(new_column)
            continue

        if operation.type == "delete_column":
            column = _find_column(board, operation.column_id)
            # Delete all cards in the column
            for card_id in column["cardIds"]:
                if card_id in board["cards"]:
                    del board["cards"][card_id]
            board["columns"] = [c for c in board["columns"] if c["id"] != operation.column_id]
            if not board["columns"]:
                raise ValueError("Cannot delete the last column")
            continue

        if operation.type == "move_column":
            column = _find_column(board, operation.column_id)
            board["columns"] = [c for c in board["columns"] if c["id"] != operation.column_id]
            pos = max(0, min(operation.position, len(board["columns"])))
            board["columns"].insert(pos, column)
            continue

        if operation.type == "add_comment":
            card = board["cards"].get(operation.card_id)
            if card is None:
                raise ValueError(f"Unknown card_id: {operation.card_id}")
            if "comments" not in card or card["comments"] is None:
                card["comments"] = []
            comment_id = f"cmt-{len(card['comments']) + 1}"
            card["comments"].append({
                "id": comment_id,
                "text": operation.text,
                "author": operation.author,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
            continue

        if operation.type == "delete_comment":
            card = board["cards"].get(operation.card_id)
            if card is None:
                raise ValueError(f"Unknown card_id: {operation.card_id}")
            comments = card.get("comments") or []
            if not any(c["id"] == operation.comment_id for c in comments):
                raise ValueError(f"Unknown comment_id: {operation.comment_id}")
            card["comments"] = [c for c in comments if c["id"] != operation.comment_id]
            continue

        if operation.type == "add_checklist_item":
            card = board["cards"].get(operation.card_id)
            if card is None:
                raise ValueError(f"Unknown card_id: {operation.card_id}")
            if "checklist" not in card or card["checklist"] is None:
                card["checklist"] = []
            item_id = f"chk-{len(card['checklist']) + 1}"
            card["checklist"].append({
                "id": item_id,
                "text": operation.text,
                "done": False,
            })
            continue

        if operation.type == "toggle_checklist_item":
            card = board["cards"].get(operation.card_id)
            if card is None:
                raise ValueError(f"Unknown card_id: {operation.card_id}")
            checklist = card.get("checklist") or []
            found = False
            for item in checklist:
                if item["id"] == operation.item_id:
                    item["done"] = not item["done"]
                    found = True
                    break
            if not found:
                raise ValueError(f"Unknown checklist item_id: {operation.item_id}")
            continue

        if operation.type == "delete_checklist_item":
            card = board["cards"].get(operation.card_id)
            if card is None:
                raise ValueError(f"Unknown card_id: {operation.card_id}")
            checklist = card.get("checklist") or []
            if not any(item["id"] == operation.item_id for item in checklist):
                raise ValueError(f"Unknown checklist item_id: {operation.item_id}")
            card["checklist"] = [item for item in checklist if item["id"] != operation.item_id]
            continue

    # Reuse BoardPayload validation before persisting the update.
    return BoardPayload.model_validate(board).model_dump()
