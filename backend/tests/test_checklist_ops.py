import pytest

from app.board_ops import apply_board_operations
from app.models import (
    AddChecklistItemOperation,
    DeleteChecklistItemOperation,
    ToggleChecklistItemOperation,
)


def _make_board(cards=None) -> dict:
    if cards is None:
        cards = {
            "card-1": {"id": "card-1", "title": "Task A", "details": "Details A"},
        }
    return {
        "columns": [{"id": "col-1", "title": "Todo", "cardIds": list(cards.keys())}],
        "cards": cards,
    }


def test_add_checklist_item() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        AddChecklistItemOperation(type="add_checklist_item", card_id="card-1", text="Buy groceries"),
    ])
    checklist = result["cards"]["card-1"]["checklist"]
    assert len(checklist) == 1
    assert checklist[0]["text"] == "Buy groceries"
    assert checklist[0]["done"] is False
    assert checklist[0]["id"] == "chk-1"


def test_add_multiple_checklist_items() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        AddChecklistItemOperation(type="add_checklist_item", card_id="card-1", text="Step 1"),
        AddChecklistItemOperation(type="add_checklist_item", card_id="card-1", text="Step 2"),
        AddChecklistItemOperation(type="add_checklist_item", card_id="card-1", text="Step 3"),
    ])
    checklist = result["cards"]["card-1"]["checklist"]
    assert len(checklist) == 3
    assert checklist[0]["id"] == "chk-1"
    assert checklist[1]["id"] == "chk-2"
    assert checklist[2]["id"] == "chk-3"


def test_add_checklist_item_unknown_card_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown card_id"):
        apply_board_operations(board, [
            AddChecklistItemOperation(type="add_checklist_item", card_id="card-missing", text="X"),
        ])


def test_toggle_checklist_item() -> None:
    board = _make_board()
    with_item = apply_board_operations(board, [
        AddChecklistItemOperation(type="add_checklist_item", card_id="card-1", text="Toggle me"),
    ])
    assert with_item["cards"]["card-1"]["checklist"][0]["done"] is False

    toggled = apply_board_operations(with_item, [
        ToggleChecklistItemOperation(type="toggle_checklist_item", card_id="card-1", item_id="chk-1"),
    ])
    assert toggled["cards"]["card-1"]["checklist"][0]["done"] is True

    toggled_back = apply_board_operations(toggled, [
        ToggleChecklistItemOperation(type="toggle_checklist_item", card_id="card-1", item_id="chk-1"),
    ])
    assert toggled_back["cards"]["card-1"]["checklist"][0]["done"] is False


def test_toggle_checklist_unknown_card_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown card_id"):
        apply_board_operations(board, [
            ToggleChecklistItemOperation(type="toggle_checklist_item", card_id="card-missing", item_id="chk-1"),
        ])


def test_toggle_checklist_unknown_item_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown checklist item_id"):
        apply_board_operations(board, [
            ToggleChecklistItemOperation(type="toggle_checklist_item", card_id="card-1", item_id="chk-missing"),
        ])


def test_delete_checklist_item() -> None:
    board = _make_board()
    with_items = apply_board_operations(board, [
        AddChecklistItemOperation(type="add_checklist_item", card_id="card-1", text="Keep"),
        AddChecklistItemOperation(type="add_checklist_item", card_id="card-1", text="Delete me"),
    ])
    result = apply_board_operations(with_items, [
        DeleteChecklistItemOperation(type="delete_checklist_item", card_id="card-1", item_id="chk-2"),
    ])
    checklist = result["cards"]["card-1"]["checklist"]
    assert len(checklist) == 1
    assert checklist[0]["text"] == "Keep"


def test_delete_checklist_unknown_card_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown card_id"):
        apply_board_operations(board, [
            DeleteChecklistItemOperation(type="delete_checklist_item", card_id="card-missing", item_id="chk-1"),
        ])


def test_delete_checklist_unknown_item_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown checklist item_id"):
        apply_board_operations(board, [
            DeleteChecklistItemOperation(type="delete_checklist_item", card_id="card-1", item_id="chk-missing"),
        ])


def test_checklist_preserved_on_edit() -> None:
    """Checklist items survive other card operations."""
    from app.models import EditCardOperation
    board = _make_board()
    with_checklist = apply_board_operations(board, [
        AddChecklistItemOperation(type="add_checklist_item", card_id="card-1", text="Survive"),
    ])
    edited = apply_board_operations(with_checklist, [
        EditCardOperation(type="edit_card", card_id="card-1", title="New Title"),
    ])
    assert edited["cards"]["card-1"]["title"] == "New Title"
    assert len(edited["cards"]["card-1"]["checklist"]) == 1
    assert edited["cards"]["card-1"]["checklist"][0]["text"] == "Survive"
