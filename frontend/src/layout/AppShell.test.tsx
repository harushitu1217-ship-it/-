import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import { AppShell } from "./AppShell";

test("renders professional operations navigation", () => {
  render(
    <AppShell currentPage="create" onNavigate={() => undefined} user={{ id: "1", username: "admin", role: "admin", is_active: true }} onLogout={() => undefined}>
      <p>页面内容</p>
    </AppShell>,
  );

  expect(screen.getByRole("heading", { name: "明景内容运营助手" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "内容创作" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "发布任务" })).toBeInTheDocument();
  expect(screen.getByText("admin · 管理员")).toBeInTheDocument();
});
