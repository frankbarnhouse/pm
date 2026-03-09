import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { AddColumnButton } from "@/components/AddColumnButton";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("AddColumnButton", () => {
  it("renders add column button", () => {
    render(<AddColumnButton onAdd={vi.fn()} />);
    expect(screen.getByTestId("add-column-btn")).toBeInTheDocument();
    expect(screen.getByText(/add column/i)).toBeInTheDocument();
  });

  it("shows form when button is clicked", async () => {
    render(<AddColumnButton onAdd={vi.fn()} />);
    await userEvent.click(screen.getByTestId("add-column-btn"));
    expect(screen.getByPlaceholderText(/column title/i)).toBeInTheDocument();
  });

  it("calls onAdd with title when form is submitted", async () => {
    const onAdd = vi.fn();
    render(<AddColumnButton onAdd={onAdd} />);
    await userEvent.click(screen.getByTestId("add-column-btn"));
    await userEvent.type(screen.getByPlaceholderText(/column title/i), "Review");
    await userEvent.click(screen.getByRole("button", { name: /^add$/i }));
    expect(onAdd).toHaveBeenCalledWith("Review");
  });

  it("hides form when cancel is clicked", async () => {
    render(<AddColumnButton onAdd={vi.fn()} />);
    await userEvent.click(screen.getByTestId("add-column-btn"));
    expect(screen.getByPlaceholderText(/column title/i)).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: /cancel/i }));
    expect(screen.queryByPlaceholderText(/column title/i)).not.toBeInTheDocument();
  });

  it("resets form after successful add", async () => {
    const onAdd = vi.fn();
    render(<AddColumnButton onAdd={onAdd} />);
    await userEvent.click(screen.getByTestId("add-column-btn"));
    await userEvent.type(screen.getByPlaceholderText(/column title/i), "Test");
    await userEvent.click(screen.getByRole("button", { name: /^add$/i }));
    // After submit, should show the button again
    expect(screen.getByTestId("add-column-btn")).toBeInTheDocument();
  });
});
