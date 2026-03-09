from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator


class CardPayload(BaseModel):
    id: str
    title: str
    details: str


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


BoardOperation = Annotated[
    CreateCardOperation
    | EditCardOperation
    | MoveCardOperation
    | DeleteCardOperation
    | RenameColumnOperation,
    Field(discriminator="type"),
]


class BoardUpdatePayload(BaseModel):
    operations: list[BoardOperation]


class AIChatResultPayload(BaseModel):
    assistant_message: str
    board_update: BoardUpdatePayload | None = None
