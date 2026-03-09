import pytest

from app.board_ops import apply_board_operations
from app.models import (
    AddColumnOperation,
    AddCommentOperation,
    CreateCardOperation,
    DeleteCardOperation,
    DeleteColumnOperation,
    DeleteCommentOperation,
    EditCardOperation,
    MoveCardOperation,
    MoveColumnOperation,
    RenameColumnOperation,
)


def _make_board(
    columns=None,
    cards=None,
) -> dict:
    if columns is None:
        columns = [
            {"id": "col-1", "title": "Todo", "cardIds": ["card-1"]},
            {"id": "col-2", "title": "Done", "cardIds": ["card-2"]},
        ]
    if cards is None:
        cards = {
            "card-1": {"id": "card-1", "title": "Task A", "details": "Details A"},
            "card-2": {"id": "card-2", "title": "Task B", "details": "Details B"},
        }
    return {"columns": columns, "cards": cards}


def test_create_card_assigns_next_id() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        CreateCardOperation(type="create_card", column_id="col-1", title="New", details="Desc"),
    ])
    assert "card-3" in result["cards"]
    assert result["cards"]["card-3"]["title"] == "New"
    assert "card-3" in result["columns"][0]["cardIds"]


def test_create_card_unknown_column_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown column_id"):
        apply_board_operations(board, [
            CreateCardOperation(type="create_card", column_id="col-missing", title="X", details="Y"),
        ])


def test_edit_card_updates_title_only() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        EditCardOperation(type="edit_card", card_id="card-1", title="Updated"),
    ])
    assert result["cards"]["card-1"]["title"] == "Updated"
    assert result["cards"]["card-1"]["details"] == "Details A"


def test_edit_card_updates_details_only() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        EditCardOperation(type="edit_card", card_id="card-1", details="New details"),
    ])
    assert result["cards"]["card-1"]["title"] == "Task A"
    assert result["cards"]["card-1"]["details"] == "New details"


def test_edit_card_unknown_id_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown card_id"):
        apply_board_operations(board, [
            EditCardOperation(type="edit_card", card_id="card-missing", title="X"),
        ])


def test_move_card_between_columns() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        MoveCardOperation(type="move_card", card_id="card-1", to_column_id="col-2"),
    ])
    assert "card-1" not in result["columns"][0]["cardIds"]
    assert "card-1" in result["columns"][1]["cardIds"]


def test_move_card_with_before_card_id() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        MoveCardOperation(type="move_card", card_id="card-1", to_column_id="col-2", before_card_id="card-2"),
    ])
    assert result["columns"][1]["cardIds"] == ["card-1", "card-2"]


def test_move_card_unknown_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown card_id"):
        apply_board_operations(board, [
            MoveCardOperation(type="move_card", card_id="card-missing", to_column_id="col-2"),
        ])


def test_move_card_unknown_destination_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown column_id"):
        apply_board_operations(board, [
            MoveCardOperation(type="move_card", card_id="card-1", to_column_id="col-missing"),
        ])


def test_delete_card_removes_from_board() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        DeleteCardOperation(type="delete_card", card_id="card-1"),
    ])
    assert "card-1" not in result["cards"]
    assert "card-1" not in result["columns"][0]["cardIds"]


def test_delete_card_unknown_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown card_id"):
        apply_board_operations(board, [
            DeleteCardOperation(type="delete_card", card_id="card-missing"),
        ])


def test_rename_column() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        RenameColumnOperation(type="rename_column", column_id="col-1", title="In Progress"),
    ])
    assert result["columns"][0]["title"] == "In Progress"


def test_rename_column_unknown_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown column_id"):
        apply_board_operations(board, [
            RenameColumnOperation(type="rename_column", column_id="col-missing", title="X"),
        ])


def test_add_column_appends_to_end() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        AddColumnOperation(type="add_column", title="Review"),
    ])
    assert len(result["columns"]) == 3
    assert result["columns"][2]["title"] == "Review"
    assert result["columns"][2]["cardIds"] == []


def test_add_column_at_position() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        AddColumnOperation(type="add_column", title="In Progress", position=1),
    ])
    assert len(result["columns"]) == 3
    assert result["columns"][1]["title"] == "In Progress"


def test_add_column_at_position_zero() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        AddColumnOperation(type="add_column", title="First", position=0),
    ])
    assert result["columns"][0]["title"] == "First"


def test_add_column_generates_unique_id() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        AddColumnOperation(type="add_column", title="Col A"),
        AddColumnOperation(type="add_column", title="Col B"),
    ])
    col_ids = [c["id"] for c in result["columns"]]
    assert len(set(col_ids)) == len(col_ids)


def test_delete_column_removes_column_and_cards() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        DeleteColumnOperation(type="delete_column", column_id="col-1"),
    ])
    assert len(result["columns"]) == 1
    assert result["columns"][0]["id"] == "col-2"
    assert "card-1" not in result["cards"]
    assert "card-2" in result["cards"]


def test_delete_column_unknown_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown column_id"):
        apply_board_operations(board, [
            DeleteColumnOperation(type="delete_column", column_id="col-missing"),
        ])


def test_delete_last_column_raises() -> None:
    board = _make_board(
        columns=[{"id": "col-1", "title": "Only", "cardIds": []}],
        cards={},
    )
    with pytest.raises(ValueError, match="Cannot delete the last column"):
        apply_board_operations(board, [
            DeleteColumnOperation(type="delete_column", column_id="col-1"),
        ])


def test_multiple_operations_applied_in_sequence() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        CreateCardOperation(type="create_card", column_id="col-1", title="X", details="Y"),
        MoveCardOperation(type="move_card", card_id="card-1", to_column_id="col-2"),
        RenameColumnOperation(type="rename_column", column_id="col-1", title="Waiting"),
    ])
    assert "card-3" in result["cards"]
    assert "card-1" in result["columns"][1]["cardIds"]
    assert result["columns"][0]["title"] == "Waiting"


def test_operations_do_not_mutate_original_board() -> None:
    board = _make_board()
    original_cards = set(board["cards"].keys())
    apply_board_operations(board, [
        DeleteCardOperation(type="delete_card", card_id="card-1"),
    ])
    assert set(board["cards"].keys()) == original_cards


def test_card_with_priority_and_due_date_preserved() -> None:
    board = _make_board(
        columns=[{"id": "col-1", "title": "Todo", "cardIds": ["card-1"]}],
        cards={
            "card-1": {
                "id": "card-1",
                "title": "Task",
                "details": "Details",
                "priority": "high",
                "due_date": "2025-12-31",
            }
        },
    )
    result = apply_board_operations(board, [
        EditCardOperation(type="edit_card", card_id="card-1", title="Updated"),
    ])
    assert result["cards"]["card-1"]["priority"] == "high"
    assert result["cards"]["card-1"]["due_date"] == "2025-12-31"


def test_move_column_to_position_zero() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        MoveColumnOperation(type="move_column", column_id="col-2", position=0),
    ])
    assert result["columns"][0]["id"] == "col-2"
    assert result["columns"][1]["id"] == "col-1"


def test_move_column_to_end() -> None:
    board = _make_board(
        columns=[
            {"id": "col-1", "title": "A", "cardIds": []},
            {"id": "col-2", "title": "B", "cardIds": []},
            {"id": "col-3", "title": "C", "cardIds": []},
        ],
        cards={},
    )
    result = apply_board_operations(board, [
        MoveColumnOperation(type="move_column", column_id="col-1", position=2),
    ])
    assert result["columns"][0]["id"] == "col-2"
    assert result["columns"][1]["id"] == "col-3"
    assert result["columns"][2]["id"] == "col-1"


def test_move_column_preserves_cards() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        MoveColumnOperation(type="move_column", column_id="col-1", position=1),
    ])
    assert result["columns"][1]["id"] == "col-1"
    assert "card-1" in result["columns"][1]["cardIds"]


def test_move_column_unknown_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown column_id"):
        apply_board_operations(board, [
            MoveColumnOperation(type="move_column", column_id="col-missing", position=0),
        ])


def test_move_column_clamps_position() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        MoveColumnOperation(type="move_column", column_id="col-1", position=100),
    ])
    assert result["columns"][-1]["id"] == "col-1"


def test_add_comment_to_card() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        AddCommentOperation(type="add_comment", card_id="card-1", text="Looks good", author="Alice"),
    ])
    comments = result["cards"]["card-1"]["comments"]
    assert len(comments) == 1
    assert comments[0]["text"] == "Looks good"
    assert comments[0]["author"] == "Alice"
    assert comments[0]["id"] == "cmt-1"


def test_add_multiple_comments() -> None:
    board = _make_board()
    result = apply_board_operations(board, [
        AddCommentOperation(type="add_comment", card_id="card-1", text="First", author="Alice"),
        AddCommentOperation(type="add_comment", card_id="card-1", text="Second", author="Bob"),
    ])
    comments = result["cards"]["card-1"]["comments"]
    assert len(comments) == 2
    assert comments[0]["id"] == "cmt-1"
    assert comments[1]["id"] == "cmt-2"


def test_add_comment_unknown_card_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown card_id"):
        apply_board_operations(board, [
            AddCommentOperation(type="add_comment", card_id="card-missing", text="X", author="A"),
        ])


def test_delete_comment() -> None:
    board = _make_board()
    # First add a comment
    board_with_comment = apply_board_operations(board, [
        AddCommentOperation(type="add_comment", card_id="card-1", text="To delete", author="Alice"),
    ])
    result = apply_board_operations(board_with_comment, [
        DeleteCommentOperation(type="delete_comment", card_id="card-1", comment_id="cmt-1"),
    ])
    assert len(result["cards"]["card-1"]["comments"]) == 0


def test_delete_comment_unknown_card_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown card_id"):
        apply_board_operations(board, [
            DeleteCommentOperation(type="delete_comment", card_id="card-missing", comment_id="cmt-1"),
        ])


def test_delete_comment_unknown_comment_raises() -> None:
    board = _make_board()
    with pytest.raises(ValueError, match="Unknown comment_id"):
        apply_board_operations(board, [
            DeleteCommentOperation(type="delete_comment", card_id="card-1", comment_id="cmt-missing"),
        ])
