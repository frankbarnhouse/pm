vi.mock("next/font/google", () => ({
  Space_Grotesk: () => ({ variable: "font-display" }),
  Manrope: () => ({ variable: "font-body" }),
}));

import RootLayout, { metadata } from "@/app/layout";

describe("RootLayout", () => {
  it("renders child content", () => {
    const element = RootLayout({ children: <div>Child content</div> });
    expect(element.props.lang).toBe("en");
  });

  it("defines metadata", () => {
    expect(metadata.title).toBe("Kanban Studio");
  });
});
