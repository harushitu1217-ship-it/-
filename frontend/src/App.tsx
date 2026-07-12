import { useEffect, useState } from "react";
import { fetchBootstrap } from "./api";
import { HistoryPanel } from "./components/HistoryPanel";
import { ProfileEditor } from "./components/ProfileEditor";
import { SettingsPage } from "./components/SettingsPage";
import { PlatformTemplatePage, PublishPrepPage, TopicLibraryPage } from "./components/StrategyPages";
import { Workspace } from "./components/Workspace";
import type { BootstrapData } from "./types";

const FALLBACK_BOOTSTRAP: BootstrapData = {
  company: {
    name: "明景绳带有限公司",
    summary: "绳带、织带和服装辅料定制源头厂家。",
    advantages: ["厂家直销", "支持来样定制", "颜色规格齐全", "交期快", "可打样"],
    industries: ["服装", "鞋帽", "箱包", "礼品包装", "宠物用品"],
    contact_note: "欢迎带样品、规格、颜色或应用场景咨询定制。",
    banned_phrases: ["保证排名第一"],
  },
  products: [],
  publish_links: {},
};

type AppPage = "home" | "create" | "topics" | "templates" | "publishPrep" | "settings" | "history";

const NAV_ITEMS: Array<{ id: AppPage; label: string }> = [
  { id: "home", label: "首页" },
  { id: "create", label: "创作中心" },
  { id: "topics", label: "话题库" },
  { id: "templates", label: "平台模板" },
  { id: "publishPrep", label: "自动上传准备" },
  { id: "settings", label: "设置" },
  { id: "history", label: "历史记录" },
];

export default function App() {
  const [bootstrap, setBootstrap] = useState<BootstrapData>(FALLBACK_BOOTSTRAP);
  const [notice, setNotice] = useState("");
  const [page, setPage] = useState<AppPage>("create");

  useEffect(() => {
    let active = true;

    fetchBootstrap()
      .then((data) => {
        if (active) {
          setBootstrap(data);
        }
      })
      .catch(() => {
        if (active) {
          setNotice("后端暂未连接，页面已显示默认资料。启动后端后可正常生成。");
        }
      });

    return () => {
      active = false;
    };
  }, []);

  function renderPage() {
    if (page === "home") {
      return (
        <div className="home-grid">
          <section className="page-panel home-hero">
            <h2>今日内容工作台</h2>
            <p>先选产品和平台生成软文，再按平台模板调整标题、排版和话题侧重。</p>
            <button type="button" className="primary-button compact-button" onClick={() => setPage("create")}>
              开始创作
            </button>
          </section>
          <ProfileEditor company={bootstrap.company} products={bootstrap.products} />
          <HistoryPanel />
        </div>
      );
    }
    if (page === "topics") return <TopicLibraryPage />;
    if (page === "templates") return <PlatformTemplatePage />;
    if (page === "publishPrep") return <PublishPrepPage />;
    if (page === "settings") return <SettingsPage />;
    if (page === "history") return <HistoryPanel />;
    return <Workspace bootstrap={bootstrap} />;
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="topbar-inner">
          <h1>明景内容运营助手</h1>
          <p>先生成图文软文，围绕绳子、织带、绳带定制和服装辅料做搜索内容沉淀。</p>
          <nav className="app-nav" aria-label="主导航">
            {NAV_ITEMS.map((item) => (
              <button
                type="button"
                key={item.id}
                className={page === item.id ? "active" : ""}
                onClick={() => setPage(item.id)}
              >
                {item.label}
              </button>
            ))}
          </nav>
        </div>
      </header>

      {notice ? <div className="notice">{notice}</div> : null}

      <section className="layout">
        <div className="main-column">{renderPage()}</div>
      </section>
    </main>
  );
}
