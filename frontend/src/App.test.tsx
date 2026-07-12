import "@testing-library/jest-dom/vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, vi } from "vitest";
import App from "./App";

afterEach(() => {
  vi.restoreAllMocks();
});

beforeEach(() => {
  localStorage.setItem("mingjing_access_token", "test-token");
  localStorage.setItem("mingjing_user", JSON.stringify({ id: "1", username: "admin", role: "admin", is_active: true }));
});

test("renders the Mingjing content assistant workspace", async () => {
  render(<App />);
  expect(screen.getByText("绳带内容工作台")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "首页" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "创作中心" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "话题库" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "平台模板" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "自动上传准备" })).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "设置" })).toBeInTheDocument();
  expect(await screen.findByText("多平台搜索铺文")).toBeInTheDocument();
  expect(await screen.findByText("产品搜索介绍型")).toBeInTheDocument();
  expect(screen.queryByText("产品介绍生成")).not.toBeInTheDocument();
  expect(screen.queryByText("豆包搜索软文")).not.toBeInTheDocument();
  expect(await screen.findByLabelText("搜索关键词")).toBeInTheDocument();
  expect(await screen.findByRole("button", { name: "生成内容" })).toBeInTheDocument();
  expect(screen.queryByLabelText("API 地址")).not.toBeInTheDocument();
});

test("shows search visibility goal without displaying banned ranking claims", async () => {
  render(<App />);

  expect(await screen.findByText(/发布到各平台后提升豆包搜索可见度/)).toBeInTheDocument();
  expect(screen.queryByText(/保证排名第一/)).not.toBeInTheDocument();
});

test("uses free text search term as the generated introduction topic", async () => {
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    if (url.endsWith("/api/bootstrap")) {
      return new Response(
        JSON.stringify({
          company: {
            name: "明景绳带有限公司",
            summary: "绳带厂家",
            advantages: [],
            industries: [],
            contact_note: "",
            banned_phrases: [],
          },
          products: [],
          publish_links: {},
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url.endsWith("/api/generate")) {
      const payload = JSON.parse(String(init?.body));
      expect(payload.product_name).toBe("麻绳");
      expect(payload.content_type).toBe("product_intro");
      return new Response(
        JSON.stringify({
          contents: [
            {
              platform: "xiaohongshu",
              title: "麻绳是什么",
              body: "麻绳是什么：这里是麻绳特点和用处。",
              tags: ["麻绳"],
              keywords: ["麻绳"],
              image_suggestions: [],
              publish_tip: "",
              optional_script: null,
              image_assets: [],
            },
          ],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    return new Response("not found", { status: 404 });
  });
  const user = userEvent.setup();
  render(<App />);

  const input = await screen.findByLabelText("搜索介绍词");
  await user.clear(input);
  await user.type(input, "麻绳");
  await user.click(await screen.findByRole("button", { name: "生成内容" }));

  expect(await screen.findByText("麻绳是什么")).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalled();
});

test("renders AI API configuration fields on the settings page", async () => {
  const user = userEvent.setup();
  render(<App />);

  await user.click(screen.getByRole("button", { name: "设置" }));

  expect(await screen.findByLabelText("API 地址")).toBeInTheDocument();
  expect(await screen.findByLabelText("API Key")).toBeInTheDocument();
  expect(await screen.findByLabelText("模型名称")).toBeInTheDocument();
  expect(await screen.findByText("平台扫码授权")).toBeInTheDocument();
  expect(await screen.findByLabelText("选择平台")).toBeInTheDocument();
  expect(await screen.findByLabelText("App ID / Client ID")).toBeInTheDocument();
  expect(await screen.findByLabelText("App Secret")).toBeInTheDocument();
  expect(await screen.findByRole("button", { name: "保存平台授权配置" })).toBeInTheDocument();
});

test("renders platform-specific templates and expanded hot topic library pages", async () => {
  const user = userEvent.setup();
  render(<App />);

  await user.click(screen.getByRole("button", { name: "平台模板" }));

  expect(await screen.findByText("小红书")).toBeInTheDocument();
  expect(screen.getByText(/真实经验/)).toBeInTheDocument();
  expect(screen.getByText("抖音图文")).toBeInTheDocument();
  expect(screen.getByText(/开头抓人/)).toBeInTheDocument();
  expect(screen.getByText("快手图文")).toBeInTheDocument();
  expect(screen.getByText(/老板口吻/)).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "话题库" }));

  expect((await screen.findAllByText(/绳带厂家怎么选/)).length).toBeGreaterThan(0);
  expect(screen.getByText(/织带定制注意什么/)).toBeInTheDocument();
  expect(screen.getAllByText("爆款话题").length).toBeGreaterThan(0);
  expect(screen.getAllByText(/热度/).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/标题方向/).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/发布建议/).length).toBeGreaterThan(0);
});

test("renders automatic publishing preparation checklist", async () => {
  const user = userEvent.setup();
  render(<App />);

  await user.click(screen.getByRole("button", { name: "自动上传准备" }));

  expect((await screen.findAllByText("自动上传准备")).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/小红书/).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/抖音图文/).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/授权状态/).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/图片上传/).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/文案字段/).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/话题标签/).length).toBeGreaterThan(0);
  expect(screen.getAllByText(/发布入口/).length).toBeGreaterThan(0);
  expect(screen.getAllByRole("button", { name: /扫码授权/ }).length).toBeGreaterThan(0);
  expect(screen.getAllByRole("link", { name: "去开放平台申请" }).length).toBeGreaterThan(0);
});

test("uploads images and separates text from image upload order in results", async () => {
  const uploadedAsset = {
    id: "asset-1.png",
    url: "/uploads/asset-1.png",
    original_name: "sample.png",
    content_type: "image/png",
  };
  const fetchMock = vi.spyOn(globalThis, "fetch").mockImplementation(async (input, init) => {
    const url = String(input);
    if (url.endsWith("/api/bootstrap")) {
      return new Response(
        JSON.stringify({
          company: {
            name: "明景绳带有限公司",
            summary: "绳带厂家",
            advantages: [],
            industries: [],
            contact_note: "",
            banned_phrases: [],
          },
          products: [],
          publish_links: {},
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    if (url.endsWith("/api/ai-config")) {
      return new Response(JSON.stringify({ configured: true, api_url: "x", model: "m", api_key_hint: "已保存" }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (url.endsWith("/api/assets/images")) {
      expect(init?.body).toBeInstanceOf(FormData);
      return new Response(JSON.stringify(uploadedAsset), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    }
    if (url.endsWith("/api/generate")) {
      const payload = JSON.parse(String(init?.body));
      expect(payload.image_assets).toEqual([uploadedAsset]);
      return new Response(
        JSON.stringify({
          contents: [
            {
              platform: "douyin",
              title: "帽绳图文标题",
              body: "这里是单独复制的文案正文",
              tags: ["帽绳"],
              keywords: ["帽绳"],
              image_suggestions: ["第1张用产品细节图"],
              publish_tip: "图片和文字分开上传",
              optional_script: null,
              image_assets: [uploadedAsset],
            },
          ],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      );
    }
    return new Response("not found", { status: 404 });
  });
  const user = userEvent.setup();
  render(<App />);

  const file = new File(["image"], "sample.png", { type: "image/png" });
  await user.upload(await screen.findByLabelText("上传产品图片"), file);
  await user.click(await screen.findByRole("button", { name: "生成内容" }));

  expect(await screen.findByText("图片上传顺序")).toBeInTheDocument();
  expect(screen.getByText("1. sample.png")).toBeInTheDocument();
  expect(screen.getByText(/文字内容/)).toBeInTheDocument();
  expect(fetchMock).toHaveBeenCalled();
});
