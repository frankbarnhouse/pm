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

  it("saves priority and due date from modal", async () => {
    const onUpdateCard = vi.fn();
    render(
      <KanbanCard
        card={{ id: "c1", title: "Editable", details: "info" }}
        onDelete={vi.fn()}
        onUpdateCard={onUpdateCard}
      />
    );
    await userEvent.click(screen.getByRole("button", { name: /edit details for editable/i }));
    await userEvent.selectOptions(screen.getByLabelText(/priority/i), "high");
    // Change due date
    const dateInput = screen.getByLabelText(/due date/i);
    await userEvent.clear(dateInput);
    await userEvent.type(dateInput, "2026-12-25");
    await userEvent.click(screen.getByRole("button", { name: /save/i }));
    expect(onUpdateCard).toHaveBeenCalledWith("c1", {
      priority: "high",
      due_date: "2026-12-25",
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
      priority: null,
      due_date: null,
    });
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
});
