import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

// Stub dnd-kit to avoid DndContext requirement
vi.mock("@dnd-kit/core", () => ({
  useDroppable: () => ({ setNodeRef: () => {}, isOver: false }),
}));
vi.mock("@dnd-kit/sortable", () => ({
  SortableContext: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  verticalListSortingStrategy: {},
  useSortable: () => ({
    attributes: {},
    listeners: {},
    setNodeRef: () => {},
    transform: null,
    transition: null,
    isDragging: false,
  }),
}));
vi.mock("@dnd-kit/utilities", () => ({
  CSS: { Transform: { toString: () => undefined } },
}));

import { KanbanColumn } from "@/components/KanbanColumn";
import type { Card, Column } from "@/lib/kanban";

afterEach(() => {
  vi.restoreAllMocks();
});

const makeColumn = (overrides?: Partial<Column>): Column => ({
  id: "col-1",
  title: "Todo",
  cardIds: ["card-1"],
  ...overrides,
});

const makeCards = (): Card[] => [
  { id: "card-1", title: "Task A", details: "Details A" },
];

describe("KanbanColumn", () => {
  it("renders column title", () => {
    render(
      <KanbanColumn
        column={makeColumn()}
        cards={makeCards()}
        columnIndex={0}
        onRename={vi.fn()}
        onAddCard={vi.fn()}
        onDeleteCard={vi.fn()}
      />
    );
    expect(screen.getByLabelText("Title for Todo")).toHaveValue("Todo");
  });

  it("shows card count badge", () => {
    render(
      <KanbanColumn
        column={makeColumn()}
        cards={makeCards()}
        columnIndex={0}
        onRename={vi.fn()}
        onAddCard={vi.fn()}
        onDeleteCard={vi.fn()}
      />
    );
    expect(screen.getByText("1")).toBeInTheDocument();
  });

  it("renders cards", () => {
    render(
      <KanbanColumn
        column={makeColumn()}
        cards={makeCards()}
        columnIndex={0}
        onRename={vi.fn()}
        onAddCard={vi.fn()}
        onDeleteCard={vi.fn()}
      />
    );
    expect(screen.getByText("Task A")).toBeInTheDocument();
  });

  it("shows empty state when no cards", () => {
    render(
      <KanbanColumn
        column={makeColumn({ cardIds: [] })}
        cards={[]}
        columnIndex={0}
        onRename={vi.fn()}
        onAddCard={vi.fn()}
        onDeleteCard={vi.fn()}
      />
    );
    expect(screen.getByText(/drop a card here/i)).toBeInTheDocument();
  });

  it("calls onRename when title is changed", async () => {
    const onRename = vi.fn();
    render(
      <KanbanColumn
        column={makeColumn()}
        cards={makeCards()}
        columnIndex={0}
        onRename={onRename}
        onAddCard={vi.fn()}
        onDeleteCard={vi.fn()}
      />
    );
    const input = screen.getByLabelText("Title for Todo");
    await userEvent.clear(input);
    await userEvent.type(input, "Done");
    expect(onRename).toHaveBeenCalled();
  });

  it("shows delete column button when onDeleteColumn is provided", () => {
    render(
      <KanbanColumn
        column={makeColumn()}
        cards={makeCards()}
        columnIndex={0}
        onRename={vi.fn()}
        onAddCard={vi.fn()}
        onDeleteCard={vi.fn()}
        onDeleteColumn={vi.fn()}
      />
    );
    expect(screen.getByTestId("delete-column-col-1")).toBeInTheDocument();
  });

  it("hides delete column button when onDeleteColumn is not provided", () => {
    render(
      <KanbanColumn
        column={makeColumn()}
        cards={makeCards()}
        columnIndex={0}
        onRename={vi.fn()}
        onAddCard={vi.fn()}
        onDeleteCard={vi.fn()}
      />
    );
    expect(screen.queryByTestId("delete-column-col-1")).not.toBeInTheDocument();
  });

  it("calls onDeleteColumn when delete button clicked", async () => {
    const onDeleteColumn = vi.fn();
    render(
      <KanbanColumn
        column={makeColumn()}
        cards={makeCards()}
        columnIndex={0}
        onRename={vi.fn()}
        onAddCard={vi.fn()}
        onDeleteCard={vi.fn()}
        onDeleteColumn={onDeleteColumn}
      />
    );
    await userEvent.click(screen.getByTestId("delete-column-col-1"));
    expect(onDeleteColumn).toHaveBeenCalledWith("col-1");
  });

  it("has correct data-testid", () => {
    render(
      <KanbanColumn
        column={makeColumn()}
        cards={makeCards()}
        columnIndex={0}
        onRename={vi.fn()}
        onAddCard={vi.fn()}
        onDeleteCard={vi.fn()}
      />
    );
    expect(screen.getByTestId("column-col-1")).toBeInTheDocument();
  });
});
