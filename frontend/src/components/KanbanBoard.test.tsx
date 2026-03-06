import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { KanbanBoard } from "@/components/KanbanBoard";
import { initialData } from "@/lib/kanban";

const getFirstColumn = () => screen.getAllByTestId(/column-/i)[0];

const waitForBoardLoad = async () => {
  await waitFor(() => {
    expect(screen.queryByText(/loading saved board/i)).not.toBeInTheDocument();
  });
};

const cloneBoard = () =>
  JSON.parse(JSON.stringify(initialData)) as typeof initialData;

const mockBoardApi = (options?: {
  chatResponse?: { assistant_message: string; board_updated: boolean };
  boardAfterChat?: typeof initialData;
}) => {
  let boardState = cloneBoard();

  const fetchMock = vi.fn(async (input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === "string" ? input : input.toString();
    const method = init?.method ?? "GET";

    if (url === "/api/chat" && method === "POST") {
      if (options?.chatResponse?.board_updated && options.boardAfterChat) {
        boardState = JSON.parse(
          JSON.stringify(options.boardAfterChat)
        ) as typeof initialData;
      }

      return new Response(
        JSON.stringify(
          options?.chatResponse ?? {
            assistant_message: "No changes needed.",
            board_updated: false,
          }
        ),
        {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    if (url === "/api/board" && method === "PUT") {
      const requestBody = JSON.parse((init?.body as string) || "{}");
      boardState = requestBody;
      return new Response(JSON.stringify({ board: requestBody }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    if (url === "/api/board") {
      return new Response(JSON.stringify({ board: boardState }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }

    return new Response(JSON.stringify({ error: "Not found" }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    });
  });

  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
};

const setupBoard = async (options?: {
  chatResponse?: { assistant_message: string; board_updated: boolean };
  boardAfterChat?: typeof initialData;
}) => {
  const fetchMock = mockBoardApi(options);
  render(<KanbanBoard />);
  await waitForBoardLoad();
  return fetchMock;
};

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("KanbanBoard", () => {
  it("renders five columns", async () => {
    await setupBoard();
    expect(screen.getAllByTestId(/column-/i)).toHaveLength(5);
  });

  it("renames a column", async () => {
    const fetchMock = await setupBoard();
    const column = getFirstColumn();
    const input = within(column).getByLabelText("Column title");
    fireEvent.change(input, { target: { value: "New Name" } });
    expect(input).toHaveValue("New Name");
    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/board",
        expect.objectContaining({ method: "PUT" })
      );
    });
  });

  it("adds and removes a card", async () => {
    await setupBoard();
    const column = getFirstColumn();
    const addButton = within(column).getByRole("button", {
      name: /add a card/i,
    });
    await userEvent.click(addButton);

    const titleInput = within(column).getByPlaceholderText(/card title/i);
    await userEvent.type(titleInput, "New card");
    const detailsInput = within(column).getByPlaceholderText(/details/i);
    await userEvent.type(detailsInput, "Notes");

    await userEvent.click(within(column).getByRole("button", { name: /add card/i }));

    expect(within(column).getByText("New card")).toBeInTheDocument();

    const deleteButton = within(column).getByRole("button", {
      name: /delete new card/i,
    });
    await userEvent.click(deleteButton);

    expect(within(column).queryByText("New card")).not.toBeInTheDocument();
  });

  it("shows a logout button", async () => {
    await setupBoard();
    const logout = screen.getByRole("button", { name: /log out/i });
    expect(logout).toBeInTheDocument();
  });

  it("renders the AI sidebar chat", async () => {
    await setupBoard();
    expect(screen.getByTestId("ai-chat-sidebar")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: /board chat/i })).toBeInTheDocument();
    expect(screen.getByText(/create, edit, move, or delete cards/i)).toBeInTheDocument();
  });

  it("sends a chat message and shows assistant response", async () => {
    await setupBoard({
      chatResponse: {
        assistant_message: "Done. I reviewed your request.",
        board_updated: false,
      },
    });

    const input = screen.getByLabelText("Message");
    await userEvent.type(input, "Review priorities for this sprint");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    expect(
      await screen.findByText("Review priorities for this sprint")
    ).toBeInTheDocument();
    expect(
      await screen.findByText("Done. I reviewed your request.")
    ).toBeInTheDocument();
  });

  it("refreshes board after AI-applied update", async () => {
    const boardAfterChat = cloneBoard();
    boardAfterChat.columns[0].title = "AI Backlog";

    const fetchMock = await setupBoard({
      chatResponse: {
        assistant_message: "Renamed backlog.",
        board_updated: true,
      },
      boardAfterChat,
    });

    await userEvent.type(screen.getByLabelText("Message"), "Rename Backlog to AI Backlog");
    await userEvent.click(screen.getByRole("button", { name: /send/i }));

    await screen.findByText("AI Backlog");
    await waitFor(() => {
      const boardGetCalls = fetchMock.mock.calls.filter(
        ([url, init]) =>
          url === "/api/board" && (!init || !init.method || init.method === "GET")
      );
      expect(boardGetCalls.length).toBeGreaterThanOrEqual(2);
    });
  });
});
