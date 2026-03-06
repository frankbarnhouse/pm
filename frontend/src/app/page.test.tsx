import { render, screen, waitFor } from "@testing-library/react";
import Home from "@/app/page";
import { initialData } from "@/lib/kanban";

beforeEach(() => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () =>
      new Response(JSON.stringify({ board: initialData }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    )
  );
});

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("Home page", () => {
  it("renders the kanban board", async () => {
    render(<Home />);
    await waitFor(() => {
      expect(screen.queryByText(/loading saved board/i)).not.toBeInTheDocument();
    });
    expect(
      screen.getByRole("heading", { name: /kanban studio/i })
    ).toBeInTheDocument();
  });
});
