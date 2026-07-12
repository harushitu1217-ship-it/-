import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { LoginPage } from "./LoginPage";

test("submits credentials and enters the workspace", async () => {
  const onLogin = vi.fn().mockResolvedValue(undefined);
  const user = userEvent.setup();
  render(<LoginPage onLogin={onLogin} />);

  await user.type(screen.getByLabelText("账号"), "admin");
  await user.type(screen.getByLabelText("密码"), "StrongPass123!");
  await user.click(screen.getByRole("button", { name: "登录" }));

  expect(onLogin).toHaveBeenCalledWith("admin", "StrongPass123!");
});

