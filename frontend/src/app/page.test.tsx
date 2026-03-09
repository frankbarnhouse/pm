import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import Home from "@/app/page";
import { initialData } from "@/lib/kanban";

const mockBoards = [
  {
    id: 1,
    title: "My First Board",
    description: "Default project board",
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-01-01T00:00:00Z",
  },
];

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL) => {
      const url = typeof input === "string" ? input : input.toString();

      if (url === "/api/boards") {
        return new Response(JSON.stringify({ boards: mockBoards }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }

      if (url.match(/\/api\/boards\/\d+$/)) {
        return new Response(
          JSON.stringify({ id: 1, title: "My First Board", description: "", board: initialData }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        );
      }

      return new Response(JSON.stringify({ error: "Not found" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      });
    })
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("Home page", () => {
  it("renders the board dashboard", async () => {
    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText("My First Board")).toBeInTheDocument();
    });
    expect(
      screen.getByRole("heading", { name: /kanban studio/i })
    ).toBeInTheDocument();
  });

  it("navigates to a board when clicked", async () => {
    render(<Home />);
    await waitFor(() => {
      expect(screen.getByText("My First Board")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByTestId("open-board-1"));
    await waitFor(() => {
      expect(screen.getByTestId("back-to-boards")).toBeInTheDocument();
    });
  });
});
