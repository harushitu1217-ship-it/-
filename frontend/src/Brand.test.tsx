import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { afterEach, test, vi } from "vitest";
import App from "./App";

afterEach(() => {
  vi.restoreAllMocks();
});

test("renders the Mingjing brand in readable Chinese", async () => {
  render(<App />);

  expect(
    await screen.findByRole("heading", { name: "明景内容运营助手" }),
  ).toBeInTheDocument();
  expect(screen.queryByText(/明璟/)).not.toBeInTheDocument();
});
