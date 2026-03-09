import { expect, test } from "@playwright/test";

const openFirstBoard = async (page: import("@playwright/test").Page) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await page.getByTestId(/^open-board-/).first().click();
  await expect(page.getByTestId("back-to-boards")).toBeVisible();
};

test("loads the board dashboard with seeded board", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.getByTestId("board-list")).toBeVisible();
  await expect(page.getByText("My First Board")).toBeVisible();
});

test("navigates into a board and shows columns", async ({ page }) => {
  await openFirstBoard(page);
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("navigates back to dashboard from board", async ({ page }) => {
  await openFirstBoard(page);
  await page.getByTestId("back-to-boards").click();
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
});

test("adds a card to a column", async ({ page }) => {
  await openFirstBoard(page);
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await openFirstBoard(page);
  const card = page.getByTestId("card-card-1");
  const targetColumn = page.getByTestId("column-col-review");
  const cardBox = await card.boundingBox();
  const columnBox = await targetColumn.boundingBox();
  if (!cardBox || !columnBox) {
    throw new Error("Unable to resolve drag coordinates.");
  }

  await page.mouse.move(
    cardBox.x + cardBox.width / 2,
    cardBox.y + cardBox.height / 2
  );
  await page.mouse.down();
  await page.mouse.move(
    columnBox.x + columnBox.width / 2,
    columnBox.y + 120,
    { steps: 12 }
  );
  await page.mouse.up();
  await expect(targetColumn.getByTestId("card-card-1")).toBeVisible();
});

test("shows search and priority filter on board", async ({ page }) => {
  await openFirstBoard(page);
  await expect(page.getByTestId("card-search")).toBeVisible();
  await expect(page.getByTestId("priority-filter")).toBeVisible();
});

test("creates a new board from dashboard", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await page.getByTestId("create-board-btn").click();
  await page.getByLabel(/board title/i).fill("E2E Test Board");
  await page.getByRole("button", { name: /create/i }).click();
  await expect(page.getByText("E2E Test Board")).toBeVisible();
});

test("applies AI chat board update and refreshes", async ({ page }) => {
  const baseBoard = {
    columns: [
      { id: "col-backlog", title: "Backlog", cardIds: ["card-1"] },
      { id: "col-discovery", title: "Discovery", cardIds: [] },
      { id: "col-progress", title: "In Progress", cardIds: [] },
      { id: "col-review", title: "Review", cardIds: [] },
      { id: "col-done", title: "Done", cardIds: [] },
    ],
    cards: {
      "card-1": {
        id: "card-1",
        title: "Plan release",
        details: "Coordinate launch tasks.",
      },
    },
  };

  const updatedBoard = {
    ...baseBoard,
    columns: baseBoard.columns.map((column) =>
      column.id === "col-review" ? { ...column, title: "QA" } : column
    ),
  };

  let boardReads = 0;

  // Intercept dashboard boards list
  await page.route("**/api/boards", async (route) => {
    if (route.request().method() === "GET") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          boards: [
            {
              id: 1,
              title: "Test Board",
              description: "",
              card_count: 1,
              column_count: 5,
              created_at: "2025-01-01T00:00:00Z",
              updated_at: "2025-01-01T00:00:00Z",
            },
          ],
        }),
      });
    } else {
      await route.continue();
    }
  });

  await page.route("**/api/boards/1", async (route) => {
    const request = route.request();
    if (request.method() === "PUT") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ board: updatedBoard }),
      });
      return;
    }

    boardReads += 1;
    const body =
      boardReads === 1
        ? { id: 1, title: "Test Board", description: "", board: baseBoard }
        : { id: 1, title: "Test Board", description: "", board: updatedBoard };
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });

  await page.route("**/api/boards/1/chat", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        assistant_message: "Renamed Review to QA.",
        board_updated: true,
      }),
    });
  });

  await page.goto("/");
  await page.getByTestId(/^open-board-/).first().click();
  await expect(page.getByTestId("back-to-boards")).toBeVisible();

  await page.getByTestId("chat-launcher").click();
  const drawer = page.getByTestId("ai-chat-drawer");
  await expect(drawer).toHaveAttribute("aria-hidden", "false");
  await drawer.getByLabel("Message").fill("Rename Review to QA");
  await drawer.getByRole("button", { name: "Send" }).click({ force: true });

  await expect(page.getByText("Renamed Review to QA.")).toBeVisible();
  await expect(
    page.getByTestId("column-col-review").locator('input[aria-label="Title for QA"]')
  ).toHaveValue("QA");
});
