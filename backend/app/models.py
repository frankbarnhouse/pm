from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


VALID_LABELS = {"bug", "feature", "improvement", "documentation", "urgent", "design", "research"}


class CardComment(BaseModel):
    id: str
    text: str
    author: str
    created_at: str


class CardPayload(BaseModel):
    id: str
    title: str
    details: str
    priority: Literal["low", "medium", "high"] | None = None
    due_date: str | None = None
    labels: list[str] | None = None
    comments: list[CardComment] | None = None


class ColumnPayload(BaseModel):
    id: str
    title: str
    cardIds: list[str]


class BoardPayload(BaseModel):
    columns: list[ColumnPayload]
    cards: dict[str, CardPayload]

    @model_validator(mode="after")
    def validate_integrity(self) -> "BoardPayload":
        column_ids = [column.id for column in self.columns]
        if len(set(column_ids)) != len(column_ids):
            raise ValueError("Column IDs must be unique")

        card_ids = set(self.cards.keys())
        all_references: list[str] = []
        for card_id, card in self.cards.items():
            if card.id != card_id:
                raise ValueError(f"Card key {card_id} must match card.id")

        for column in self.columns:
            all_references.extend(column.cardIds)

        if len(set(all_references)) != len(all_references):
            raise ValueError("A card cannot exist in multiple columns")

        unknown_ids = [card_id for card_id in all_references if card_id not in card_ids]
        if unknown_ids:
            raise ValueError(f"Unknown card IDs in columns: {unknown_ids}")

        unreferenced = card_ids.difference(all_references)
        if unreferenced:
            raise ValueError(f"Unreferenced cards are not allowed: {sorted(unreferenced)}")

        return self


class ChatMessagePayload(BaseModel):
    prompt: str

    @model_validator(mode="after")
    def validate_prompt(self) -> "ChatMessagePayload":
        if not self.prompt.strip():
            raise ValueError("Prompt cannot be empty")
        return self


class CreateCardOperation(BaseModel):
    type: Literal["create_card"]
    column_id: str
    title: str
    details: str


class EditCardOperation(BaseModel):
    type: Literal["edit_card"]
    card_id: str
    title: str | None = None
    details: str | None = None

    @model_validator(mode="after")
    def validate_has_changes(self) -> "EditCardOperation":
        if self.title is None and self.details is None:
            raise ValueError("edit_card requires title and/or details")
        return self


class MoveCardOperation(BaseModel):
    type: Literal["move_card"]
    card_id: str
    to_column_id: str
    before_card_id: str | None = None


class DeleteCardOperation(BaseModel):
    type: Literal["delete_card"]
    card_id: str


class RenameColumnOperation(BaseModel):
    type: Literal["rename_column"]
    column_id: str
    title: str


class AddColumnOperation(BaseModel):
    type: Literal["add_column"]
    title: str
    position: int | None = None


class DeleteColumnOperation(BaseModel):
    type: Literal["delete_column"]
    column_id: str


class MoveColumnOperation(BaseModel):
    type: Literal["move_column"]
    column_id: str
    position: int


class AddCommentOperation(BaseModel):
    type: Literal["add_comment"]
    card_id: str
    text: str
    author: str


class DeleteCommentOperation(BaseModel):
    type: Literal["delete_comment"]
    card_id: str
    comment_id: str


BoardOperation = Annotated[
    CreateCardOperation
    | EditCardOperation
    | MoveCardOperation
    | DeleteCardOperation
    | RenameColumnOperation
    | AddColumnOperation
    | DeleteColumnOperation
    | MoveColumnOperation
    | AddCommentOperation
    | DeleteCommentOperation,
    Field(discriminator="type"),
]


class BoardUpdatePayload(BaseModel):
    operations: list[BoardOperation]


class AIChatResultPayload(BaseModel):
    assistant_message: str
    board_update: BoardUpdatePayload | None = None


# --- Multi-board API models ---


class CreateBoardRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = ""


class UpdateBoardMetaRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = None

    @model_validator(mode="after")
    def validate_has_fields(self) -> "UpdateBoardMetaRequest":
        if self.title is None and self.description is None:
            raise ValueError("At least one of title or description is required")
        return self


# --- Registration model ---


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    password: str = Field(min_length=4, max_length=100)
    display_name: str = ""

    @model_validator(mode="after")
    def validate_username_chars(self) -> "RegisterRequest":
        if not self.username.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username may only contain letters, numbers, hyphens, and underscores")
        return self


# --- User profile models ---


class UpdateProfileRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=100)

    @model_validator(mode="after")
    def validate_has_fields(self) -> "UpdateProfileRequest":
        if self.display_name is None:
            raise ValueError("At least one field is required")
        return self


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=4, max_length=100)


class AddCommentRequest(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


class ImportBoardRequest(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str = ""
    board: dict
