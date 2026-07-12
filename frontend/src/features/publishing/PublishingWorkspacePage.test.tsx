import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { vi } from "vitest";
import { PublishingWorkspacePage } from "./PublishingWorkspacePage";

test("shows automatic and manual publishing windows together", async () => {
  vi.spyOn(globalThis, "fetch").mockResolvedValue(
    new Response(JSON.stringify({ items: [
      { id: "auto-1", content_version_id: "v1", platform: "toutiao", mode: "official", status: "queued", scheduled_at: null, retry_count: 0, external_id: null, metrics: {} },
      { id: "manual-1", content_version_id: "v2", platform: "xiaohongshu", mode: "manual", status: "ready_for_manual_publish", scheduled_at: null, retry_count: 0, external_id: null, metrics: {} },
    ] }), { status: 200, headers: { "Content-Type": "application/json" } }),
  );

  render(<PublishingWorkspacePage />);

  expect(await screen.findByRole("heading", { name: "自动发布" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "人工发布" })).toBeInTheDocument();
  expect(await screen.findByText("今日头条")).toBeInTheDocument();
  expect(await screen.findByText("小红书")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "打开人工发布包" })).toBeInTheDocument();
});
