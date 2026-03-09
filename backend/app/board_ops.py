from copy import deepcopy

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

    # Reuse BoardPayload validation before persisting the update.
    return BoardPayload.model_validate(board).model_dump()
