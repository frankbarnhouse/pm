import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { BoardDashboard } from "@/components/BoardDashboard";

const makeMockBoards = () => [
  {
    id: 1,
    title: "Sprint Board",
    description: "Weekly sprint tracking",
    archived: false,
    card_count: 5,
    column_count: 3,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-06-01T00:00:00Z",
  },
  {
    id: 2,
    title: "Product Roadmap",
    description: "",
    archived: false,
    card_count: 10,
    column_count: 4,
    created_at: "2025-01-01T00:00:00Z",
    updated_at: "2025-05-01T00:00:00Z",
  },
];

const setupDashboard = (options?: { boards?: ReturnType<typeof makeMockBoards> }) => {
  const boards = options?.boards ?? makeMockBoards();

  vi.stubGlobal(
    "fetch",
    vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
      const url = typeof input === "string" ? input : input.toString();
      const method = init?.method ?? "GET";

      if ((url === "/api/boards" || url === "/api/boards?include_archived=true") && method === "GET") {
        return new Response(JSON.stringify({ boards }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }

      if (url === "/api/boards" && method === "POST") {
        const body = JSON.parse((init?.body as string) || "{}");
        const newBoard = {
          id: 99,
          title: body.title,
          description: body.description || "",
          archived: false,
          card_count: 0,
          column_count: 4,
          created_at: "2025-06-01T00:00:00Z",
          updated_at: "2025-06-01T00:00:00Z",
        };
        boards.push(newBoard);
        return new Response(JSON.stringify({ board: newBoard }), {
          status: 201,
          headers: { "Content-Type": "application/json" },
        });
      }

      if (url.match(/\/api\/boards\/\d+$/) && method === "DELETE") {
        return new Response(JSON.stringify({ deleted: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }

      if (url.match(/\/api\/boards\/\d+\/duplicate$/) && method === "POST") {
        const newBoard = {
          id: 100,
          title: "Sprint Board (copy)",
          description: "",
          archived: false,
          card_count: 5,
          column_count: 3,
          created_at: "2025-06-01T00:00:00Z",
          updated_at: "2025-06-01T00:00:00Z",
        };
        boards.push(newBoard);
        return new Response(JSON.stringify({ board: newBoard }), {
          status: 201,
          headers: { "Content-Type": "application/json" },
        });
      }

      if (url.match(/\/api\/boards\/\d+\/archive$/) && method === "POST") {
        return new Response(JSON.stringify({ archived: true }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }

      if (url.match(/\/api\/boards\/\d+\/unarchive$/) && method === "POST") {
        return new Response(JSON.stringify({ archived: false }), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        });
      }

      if (url.match(/\/api\/boards\/\d+$/) && method === "GET") {
        return new Response(
          JSON.stringify({
            id: 1,
            title: "Sprint Board",
            board: { columns: [], cards: {} },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        );
      }

      if (url.match(/\/api\/boards\/\d+$/) && method === "PATCH") {
        return new Response(
          JSON.stringify({ board: { ...boards[0], ...JSON.parse((init?.body as string) || "{}") } }),
          { status: 200, headers: { "Content-Type": "application/json" } }
        );
      }

      return new Response(JSON.stringify({ error: "Not found" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      });
    })
  );
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("BoardDashboard", () => {
  it("renders board list", async () => {
    setupDashboard();
    render(<BoardDashboard onSelectBoard={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Sprint Board")).toBeInTheDocument();
    });
    expect(screen.getByText("Product Roadmap")).toBeInTheDocument();
  });

  it("shows header with Kanban Studio title", async () => {
    setupDashboard();
    render(<BoardDashboard onSelectBoard={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /kanban studio/i })).toBeInTheDocument();
    });
  });

  it("calls onSelectBoard when board is clicked", async () => {
    setupDashboard();
    const onSelect = vi.fn();
    render(<BoardDashboard onSelectBoard={onSelect} />);

    await waitFor(() => {
      expect(screen.getByText("Sprint Board")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByTestId("open-board-1"));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it("shows create board form when clicking new board", async () => {
    setupDashboard();
    render(<BoardDashboard onSelectBoard={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByTestId("create-board-btn")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByTestId("create-board-btn"));
    expect(screen.getByLabelText(/board title/i)).toBeInTheDocument();
  });

  it("shows empty state when no boards exist", async () => {
    setupDashboard({ boards: [] });
    render(<BoardDashboard onSelectBoard={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/no boards yet/i)).toBeInTheDocument();
    });
  });

  it("shows logout button", async () => {
    setupDashboard();
    render(<BoardDashboard onSelectBoard={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /log out/i })).toBeInTheDocument();
    });
  });

  it("shows board description when present", async () => {
    setupDashboard();
    render(<BoardDashboard onSelectBoard={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Weekly sprint tracking")).toBeInTheDocument();
    });
  });

  it("shows duplicate button for each board", async () => {
    setupDashboard();
    render(<BoardDashboard onSelectBoard={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByTestId("duplicate-board-1")).toBeInTheDocument();
    });
    expect(screen.getByTestId("duplicate-board-2")).toBeInTheDocument();
  });

  it("calls duplicate API when duplicate button clicked", async () => {
    setupDashboard();
    render(<BoardDashboard onSelectBoard={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByTestId("duplicate-board-1")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByTestId("duplicate-board-1"));

    await waitFor(() => {
      const fetchFn = fetch as ReturnType<typeof vi.fn>;
      const calls = fetchFn.mock.calls as Array<[string, RequestInit?]>;
      const duplicateCall = calls.find(
        ([url, init]) => url === "/api/boards/1/duplicate" && init?.method === "POST"
      );
      expect(duplicateCall).toBeDefined();
    });
  });

  it("shows dashboard stats with board and card counts", async () => {
    setupDashboard();
    render(<BoardDashboard onSelectBoard={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByTestId("dashboard-stats")).toBeInTheDocument();
    });
    // 2 boards, 15 total cards, 7 total columns
    expect(screen.getByText("2")).toBeInTheDocument();
    expect(screen.getByText("15")).toBeInTheDocument();
    expect(screen.getByText("7")).toBeInTheDocument();
  });

  it("does not show dashboard stats when no boards", async () => {
    setupDashboard({ boards: [] });
    render(<BoardDashboard onSelectBoard={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/no boards yet/i)).toBeInTheDocument();
    });
    expect(screen.queryByTestId("dashboard-stats")).not.toBeInTheDocument();
  });

  it("shows archive button for active boards", async () => {
    setupDashboard();
    render(<BoardDashboard onSelectBoard={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByTestId("archive-board-1")).toBeInTheDocument();
    });
  });

  it("shows export button for each board", async () => {
    setupDashboard();
    render(<BoardDashboard onSelectBoard={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByTestId("export-board-1")).toBeInTheDocument();
    });
    expect(screen.getByTestId("export-board-2")).toBeInTheDocument();
  });

  it("shows toggle archived button", async () => {
    setupDashboard();
    render(<BoardDashboard onSelectBoard={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByTestId("toggle-archived")).toBeInTheDocument();
    });
    expect(screen.getByText("Show archived")).toBeInTheDocument();
  });

  it("calls archive API when archive button clicked", async () => {
    setupDashboard();
    render(<BoardDashboard onSelectBoard={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByTestId("archive-board-1")).toBeInTheDocument();
    });
    await userEvent.click(screen.getByTestId("archive-board-1"));

    await waitFor(() => {
      const fetchFn = fetch as ReturnType<typeof vi.fn>;
      const calls = fetchFn.mock.calls as Array<[string, RequestInit?]>;
      const archiveCall = calls.find(
        ([url, init]) => url === "/api/boards/1/archive" && init?.method === "POST"
      );
      expect(archiveCall).toBeDefined();
    });
  });
});
