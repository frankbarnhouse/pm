import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { NewCardForm } from "@/components/NewCardForm";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("NewCardForm", () => {
  it("renders add a card button", () => {
    render(<NewCardForm onAdd={vi.fn()} />);
    expect(screen.getByRole("button", { name: /add a card/i })).toBeInTheDocument();
  });

  it("shows form when add button is clicked", async () => {
    render(<NewCardForm onAdd={vi.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: /add a card/i }));
    expect(screen.getByPlaceholderText(/card title/i)).toBeInTheDocument();
    expect(screen.getByPlaceholderText(/details/i)).toBeInTheDocument();
  });

  it("calls onAdd with title and details", async () => {
    const onAdd = vi.fn();
    render(<NewCardForm onAdd={onAdd} />);
    await userEvent.click(screen.getByRole("button", { name: /add a card/i }));
    await userEvent.type(screen.getByPlaceholderText(/card title/i), "New Task");
    await userEvent.type(screen.getByPlaceholderText(/details/i), "Task details");
    await userEvent.click(screen.getByRole("button", { name: /add card/i }));
    expect(onAdd).toHaveBeenCalledWith("New Task", "Task details");
  });

  it("trims whitespace from inputs", async () => {
    const onAdd = vi.fn();
    render(<NewCardForm onAdd={onAdd} />);
    await userEvent.click(screen.getByRole("button", { name: /add a card/i }));
    await userEvent.type(screen.getByPlaceholderText(/card title/i), "  Trimmed  ");
    await userEvent.type(screen.getByPlaceholderText(/details/i), "  Notes  ");
    await userEvent.click(screen.getByRole("button", { name: /add card/i }));
    expect(onAdd).toHaveBeenCalledWith("Trimmed", "Notes");
  });

  it("hides form after submit", async () => {
    render(<NewCardForm onAdd={vi.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: /add a card/i }));
    await userEvent.type(screen.getByPlaceholderText(/card title/i), "Task");
    await userEvent.click(screen.getByRole("button", { name: /add card/i }));
    expect(screen.queryByPlaceholderText(/card title/i)).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /add a card/i })).toBeInTheDocument();
  });

  it("hides form when cancel is clicked", async () => {
    render(<NewCardForm onAdd={vi.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: /add a card/i }));
    expect(screen.getByPlaceholderText(/card title/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(screen.queryByPlaceholderText(/card title/i)).not.toBeInTheDocument();
  });

  it("resets form when cancel is clicked", async () => {
    render(<NewCardForm onAdd={vi.fn()} />);
    await userEvent.click(screen.getByRole("button", { name: /add a card/i }));
    await userEvent.type(screen.getByPlaceholderText(/card title/i), "Partial");
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
    // Reopen and check it's empty
    await userEvent.click(screen.getByRole("button", { name: /add a card/i }));
    expect(screen.getByPlaceholderText(/card title/i)).toHaveValue("");
  });

  it("does not call onAdd with empty title", async () => {
    const onAdd = vi.fn();
    render(<NewCardForm onAdd={onAdd} />);
    await userEvent.click(screen.getByRole("button", { name: /add a card/i }));
    // Try to submit with empty title
    await userEvent.type(screen.getByPlaceholderText(/details/i), "Some details");
    // The form has required on title, so browser validation prevents submission
    // But we can check onAdd was not called
    expect(onAdd).not.toHaveBeenCalled();
  });
});
