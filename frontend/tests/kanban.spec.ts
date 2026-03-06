import { expect, test } from "@playwright/test";

test("loads the kanban board", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Kanban Studio" })).toBeVisible();
  await expect(page.locator('[data-testid^="column-"]')).toHaveCount(5);
});

test("adds a card to a column", async ({ page }) => {
  await page.goto("/");
  const firstColumn = page.locator('[data-testid^="column-"]').first();
  await firstColumn.getByRole("button", { name: /add a card/i }).click();
  await firstColumn.getByPlaceholder("Card title").fill("Playwright card");
  await firstColumn.getByPlaceholder("Details").fill("Added via e2e.");
  await firstColumn.getByRole("button", { name: /add card/i }).click();
  await expect(firstColumn.getByText("Playwright card")).toBeVisible();
});

test("moves a card between columns", async ({ page }) => {
  await page.goto("/");
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
  await page.route("**/api/board", async (route) => {
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
    const body = boardReads === 1 ? { board: baseBoard } : { board: updatedBoard };
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify(body),
    });
  });

  await page.route("**/api/chat", async (route) => {
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
  await page.evaluate(() => {
    const launcher = document.querySelector('[data-testid="chat-launcher"]') as HTMLButtonElement | null;
    launcher?.click();
  });
  const drawer = page.getByTestId("ai-chat-drawer");
  await expect(drawer).toHaveAttribute("aria-hidden", "false");
  await drawer.getByLabel("Message").fill("Rename Review to QA");
  await drawer.getByRole("button", { name: "Send" }).click({ force: true });

  await expect(page.getByText("Renamed Review to QA.")).toBeVisible();
  await expect(
    page.getByTestId("column-col-review").locator('input[aria-label="Column title"]')
  ).toHaveValue("QA");
});
