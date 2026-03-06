import { render, screen } from "@testing-library/react";
import Home from "@/app/page";

describe("Home page", () => {
  it("renders the kanban board", () => {
    render(<Home />);
    expect(
      screen.getByRole("heading", { name: /kanban studio/i })
    ).toBeInTheDocument();
  });
});
