import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

// Stub @dnd-kit/sortable so KanbanCard renders without DndContext
vi.mock("@dnd-kit/sortable", () => ({
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

import { KanbanCard } from "@/components/KanbanCard";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("KanbanCard", () => {
  it("renders card title and details", () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "My Task", details: "Some details" }}
        onDelete={vi.fn()}
      />
    );
    expect(screen.getByText("My Task")).toBeInTheDocument();
    expect(screen.getByText("Some details")).toBeInTheDocument();
  });

  it("renders without details when empty", () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "No Details", details: "" }}
        onDelete={vi.fn()}
      />
    );
    expect(screen.getByText("No Details")).toBeInTheDocument();
  });

  it("shows priority dot for high priority", () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "Urgent", details: "d", priority: "high" }}
        onDelete={vi.fn()}
      />
    );
    expect(screen.getByTitle("High priority")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
  });

  it("shows priority dot for medium priority", () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "Normal", details: "d", priority: "medium" }}
        onDelete={vi.fn()}
      />
    );
    expect(screen.getByTitle("Medium priority")).toBeInTheDocument();
    expect(screen.getByText("Medium")).toBeInTheDocument();
  });

  it("shows priority dot for low priority", () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "Minor", details: "d", priority: "low" }}
        onDelete={vi.fn()}
      />
    );
    expect(screen.getByTitle("Low priority")).toBeInTheDocument();
    expect(screen.getByText("Low")).toBeInTheDocument();
  });

  it("does not show priority indicator when none set", () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "Task", details: "d" }}
        onDelete={vi.fn()}
      />
    );
    expect(screen.queryByTitle(/priority/i)).not.toBeInTheDocument();
  });

  it("shows due date badge", () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "Task", details: "d", due_date: "2026-06-15" }}
        onDelete={vi.fn()}
      />
    );
    expect(screen.getByText(/jun/i)).toBeInTheDocument();
  });

  it("does not show due date when not set", () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "Task", details: "d" }}
        onDelete={vi.fn()}
      />
    );
    // No date badge should appear
    expect(screen.queryByText(/jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec/i)).not.toBeInTheDocument();
  });

  it("calls onDelete when delete button clicked", async () => {
    const onDelete = vi.fn();
    render(
      <KanbanCard
        card={{ id: "c1", title: "Doomed", details: "bye" }}
        onDelete={onDelete}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /delete doomed/i }));
    expect(onDelete).toHaveBeenCalledWith("c1");
  });

  it("shows edit button when onUpdateCard is provided", () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "Editable", details: "d" }}
        onDelete={vi.fn()}
        onUpdateCard={vi.fn()}
      />
    );
    expect(screen.getByRole("button", { name: /edit details for editable/i })).toBeInTheDocument();
  });

  it("does not show edit button without onUpdateCard", () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "ReadOnly", details: "d" }}
        onDelete={vi.fn()}
      />
    );
    expect(screen.queryByRole("button", { name: /edit details/i })).not.toBeInTheDocument();
  });

  it("opens CardDetailsModal when edit is clicked", async () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "Editable", details: "info" }}
        onDelete={vi.fn()}
        onUpdateCard={vi.fn()}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for editable/i }));
    expect(screen.getByTestId("card-details-modal")).toBeInTheDocument();
    expect(screen.getByLabelText(/^title$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^details$/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/priority/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/due date/i)).toBeInTheDocument();
  });

  it("closes modal when cancel is clicked", async () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "Editable", details: "info" }}
        onDelete={vi.fn()}
        onUpdateCard={vi.fn()}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for editable/i }));
    expect(screen.getByTestId("card-details-modal")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(screen.queryByTestId("card-details-modal")).not.toBeInTheDocument();
  });

  it("saves all fields from modal", async () => {
    const onUpdateCard = vi.fn();
    render(
      <KanbanCard
        card={{ id: "c1", title: "Editable", details: "info" }}
        onDelete={vi.fn()}
        onUpdateCard={onUpdateCard}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for editable/i }));
    // Edit title
    const titleInput = screen.getByLabelText(/^title$/i);
    await userEvent.clear(titleInput);
    await userEvent.type(titleInput, "Updated Title");
    // Edit priority
    await userEvent.selectOptions(screen.getByLabelText(/priority/i), "high");
    // Change due date
    const dateInput = screen.getByLabelText(/due date/i);
    await userEvent.clear(dateInput);
    await userEvent.type(dateInput, "2026-12-25");
    await userEvent.click(screen.getByRole("button", { name: /save/i }));
    expect(onUpdateCard).toHaveBeenCalledWith("c1", {
      title: "Updated Title",
      details: "info",
      priority: "high",
      due_date: "2026-12-25",
      labels: [],
    });
  });

  it("saves null priority when cleared", async () => {
    const onUpdateCard = vi.fn();
    render(
      <KanbanCard
        card={{ id: "c1", title: "Editable", details: "info", priority: "medium" }}
        onDelete={vi.fn()}
        onUpdateCard={onUpdateCard}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for editable/i }));
    await userEvent.selectOptions(screen.getByLabelText(/priority/i), "");
    await userEvent.click(screen.getByRole("button", { name: /save/i }));
    expect(onUpdateCard).toHaveBeenCalledWith("c1", {
      title: "Editable",
      details: "info",
      priority: null,
      due_date: null,
      labels: [],
    });
  });

  it("edits card details in modal", async () => {
    const onUpdateCard = vi.fn();
    render(
      <KanbanCard
        card={{ id: "c1", title: "Task", details: "old info" }}
        onDelete={vi.fn()}
        onUpdateCard={onUpdateCard}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for task/i }));
    const detailsInput = screen.getByLabelText(/^details$/i);
    await userEvent.clear(detailsInput);
    await userEvent.type(detailsInput, "new details");
    await userEvent.click(screen.getByRole("button", { name: /save/i }));
    expect(onUpdateCard).toHaveBeenCalledWith("c1", expect.objectContaining({
      details: "new details",
    }));
  });

  it("renders labels on card", () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "Task", details: "d", labels: ["bug", "feature"] }}
        onDelete={vi.fn()}
      />
    );
    expect(screen.getByTestId("label-bug")).toBeInTheDocument();
    expect(screen.getByTestId("label-feature")).toBeInTheDocument();
    expect(screen.getByText("Bug")).toBeInTheDocument();
    expect(screen.getByText("Feature")).toBeInTheDocument();
  });

  it("does not render labels section when none set", () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "Task", details: "d" }}
        onDelete={vi.fn()}
      />
    );
    expect(screen.queryByTestId(/^label-/)).not.toBeInTheDocument();
  });

  it("shows label picker in modal", async () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "Task", details: "d" }}
        onDelete={vi.fn()}
        onUpdateCard={vi.fn()}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for task/i }));
    expect(screen.getByTestId("label-picker")).toBeInTheDocument();
    expect(screen.getByTestId("toggle-label-bug")).toBeInTheDocument();
  });

  it("toggles labels in modal and saves them", async () => {
    const onUpdateCard = vi.fn();
    render(
      <KanbanCard
        card={{ id: "c1", title: "Task", details: "d" }}
        onDelete={vi.fn()}
        onUpdateCard={onUpdateCard}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for task/i }));
    await userEvent.click(screen.getByTestId("toggle-label-bug"));
    await userEvent.click(screen.getByTestId("toggle-label-design"));
    await userEvent.click(screen.getByRole("button", { name: /save/i }));
    const call = onUpdateCard.mock.calls[0];
    expect(call[1].labels).toContain("bug");
    expect(call[1].labels).toContain("design");
  });

  it("has correct data-testid", () => {
    render(
      <KanbanCard
        card={{ id: "card-42", title: "Task", details: "d" }}
        onDelete={vi.fn()}
      />
    );
    expect(screen.getByTestId("card-card-42")).toBeInTheDocument();
  });

  it("shows comment count badge when card has comments", () => {
    render(
      <KanbanCard
        card={{
          id: "c1",
          title: "Task",
          details: "d",
          comments: [
            { id: "cmt-1", text: "Hello", author: "Alice", created_at: "2026-01-01T00:00:00Z" },
            { id: "cmt-2", text: "World", author: "Bob", created_at: "2026-01-02T00:00:00Z" },
          ],
        }}
        onDelete={vi.fn()}
      />
    );
    expect(screen.getByTestId("comment-count")).toHaveTextContent("2");
  });

  it("does not show comment badge when no comments", () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "Task", details: "d" }}
        onDelete={vi.fn()}
      />
    );
    expect(screen.queryByTestId("comment-count")).not.toBeInTheDocument();
  });

  it("shows comments in modal", async () => {
    render(
      <KanbanCard
        card={{
          id: "c1",
          title: "Task",
          details: "d",
          comments: [
            { id: "cmt-1", text: "Great work", author: "Alice", created_at: "2026-03-01T00:00:00Z" },
          ],
        }}
        onDelete={vi.fn()}
        onUpdateCard={vi.fn()}
        onAddComment={vi.fn()}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for task/i }));
    expect(screen.getByTestId("comments-section")).toBeInTheDocument();
    expect(screen.getByTestId("comment-cmt-1")).toBeInTheDocument();
    expect(screen.getByText("Great work")).toBeInTheDocument();
    expect(screen.getByText("Alice")).toBeInTheDocument();
  });

  it("shows comment input when onAddComment is provided", async () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "Task", details: "d" }}
        onDelete={vi.fn()}
        onUpdateCard={vi.fn()}
        onAddComment={vi.fn()}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for task/i }));
    expect(screen.getByTestId("comment-input")).toBeInTheDocument();
    expect(screen.getByTestId("add-comment-btn")).toBeInTheDocument();
  });

  it("calls onAddComment when add button clicked", async () => {
    const onAddComment = vi.fn();
    render(
      <KanbanCard
        card={{ id: "c1", title: "Task", details: "d" }}
        onDelete={vi.fn()}
        onUpdateCard={vi.fn()}
        onAddComment={onAddComment}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for task/i }));
    const input = screen.getByTestId("comment-input");
    await userEvent.type(input, "New comment");
    await userEvent.click(screen.getByTestId("add-comment-btn"));
    expect(onAddComment).toHaveBeenCalledWith("c1", "New comment");
  });

  it("calls onDeleteComment when delete button clicked on a comment", async () => {
    const onDeleteComment = vi.fn();
    render(
      <KanbanCard
        card={{
          id: "c1",
          title: "Task",
          details: "d",
          comments: [
            { id: "cmt-1", text: "Remove me", author: "Alice", created_at: "2026-03-01T00:00:00Z" },
          ],
        }}
        onDelete={vi.fn()}
        onUpdateCard={vi.fn()}
        onDeleteComment={onDeleteComment}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for task/i }));
    await userEvent.click(screen.getByRole("button", { name: /delete comment by alice/i }));
    expect(onDeleteComment).toHaveBeenCalledWith("c1", "cmt-1");
  });

  it("shows checklist progress badge on card", () => {
    render(
      <KanbanCard
        card={{
          id: "c1",
          title: "Task",
          details: "d",
          checklist: [
            { id: "chk-1", text: "Step 1", done: true },
            { id: "chk-2", text: "Step 2", done: false },
            { id: "chk-3", text: "Step 3", done: true },
          ],
        }}
        onDelete={vi.fn()}
      />
    );
    expect(screen.getByTestId("checklist-progress")).toHaveTextContent("2/3");
  });

  it("does not show checklist badge when no items", () => {
    render(
      <KanbanCard
        card={{ id: "c1", title: "Task", details: "d" }}
        onDelete={vi.fn()}
      />
    );
    expect(screen.queryByTestId("checklist-progress")).not.toBeInTheDocument();
  });

  it("shows checklist section in modal", async () => {
    render(
      <KanbanCard
        card={{
          id: "c1",
          title: "Task",
          details: "d",
          checklist: [
            { id: "chk-1", text: "Write tests", done: false },
          ],
        }}
        onDelete={vi.fn()}
        onUpdateCard={vi.fn()}
        onAddChecklistItem={vi.fn()}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for task/i }));
    expect(screen.getByTestId("checklist-section")).toBeInTheDocument();
    expect(screen.getByTestId("checklist-chk-1")).toBeInTheDocument();
    expect(screen.getByText("Write tests")).toBeInTheDocument();
  });

  it("calls onAddChecklistItem when add button clicked", async () => {
    const onAddChecklistItem = vi.fn();
    render(
      <KanbanCard
        card={{ id: "c1", title: "Task", details: "d" }}
        onDelete={vi.fn()}
        onUpdateCard={vi.fn()}
        onAddChecklistItem={onAddChecklistItem}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for task/i }));
    const input = screen.getByTestId("checklist-input");
    await userEvent.type(input, "New item");
    await userEvent.click(screen.getByTestId("add-checklist-btn"));
    expect(onAddChecklistItem).toHaveBeenCalledWith("c1", "New item");
  });

  it("calls onToggleChecklistItem when checkbox clicked", async () => {
    const onToggleChecklistItem = vi.fn();
    render(
      <KanbanCard
        card={{
          id: "c1",
          title: "Task",
          details: "d",
          checklist: [{ id: "chk-1", text: "Toggle me", done: false }],
        }}
        onDelete={vi.fn()}
        onUpdateCard={vi.fn()}
        onToggleChecklistItem={onToggleChecklistItem}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for task/i }));
    await userEvent.click(screen.getByTestId("toggle-checklist-chk-1"));
    expect(onToggleChecklistItem).toHaveBeenCalledWith("c1", "chk-1");
  });

  it("calls onDeleteChecklistItem when delete button clicked", async () => {
    const onDeleteChecklistItem = vi.fn();
    render(
      <KanbanCard
        card={{
          id: "c1",
          title: "Task",
          details: "d",
          checklist: [{ id: "chk-1", text: "Delete me", done: false }],
        }}
        onDelete={vi.fn()}
        onUpdateCard={vi.fn()}
        onDeleteChecklistItem={onDeleteChecklistItem}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for task/i }));
    await userEvent.click(screen.getByRole("button", { name: /delete checklist item delete me/i }));
    expect(onDeleteChecklistItem).toHaveBeenCalledWith("c1", "chk-1");
  });
});
