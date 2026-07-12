import type { ReactNode } from "react";
import { BarChart3, Boxes, FilePenLine, Flame, LogOut, Send, Settings, Users } from "lucide-react";
import type { AuthUser } from "../features/auth/types";

export type AppPage = "create" | "catalog" | "trends" | "review" | "publishing" | "analytics" | "team" | "settings";

const ROLE_LABELS = { admin: "管理员", operator: "运营", reviewer: "审核员" } as const;
const NAV_ITEMS = [
  { id: "create", label: "内容创作", icon: FilePenLine },
  { id: "catalog", label: "产品与素材", icon: Boxes },
  { id: "trends", label: "热点中心", icon: Flame },
  { id: "review", label: "审核队列", icon: Users },
  { id: "publishing", label: "发布任务", icon: Send },
  { id: "analytics", label: "数据分析", icon: BarChart3 },
  { id: "team", label: "团队管理", icon: Users },
  { id: "settings", label: "系统设置", icon: Settings },
] as const;

export function AppShell({ currentPage, onNavigate, user, onLogout, children }: { currentPage: AppPage; onNavigate: (page: AppPage) => void; user: AuthUser; onLogout: () => void; children: ReactNode }) {
  const currentLabel = NAV_ITEMS.find((item) => item.id === currentPage)?.label ?? "工作台";
  return (
    <main className="ops-shell">
      <aside className="ops-sidebar">
        <div className="ops-brand"><strong>明景</strong><span>内容运营助手</span></div>
        <nav aria-label="主导航">
          {NAV_ITEMS.map(({ id, label, icon: Icon }) => (
            <button key={id} type="button" className={currentPage === id ? "active" : ""} onClick={() => onNavigate(id)}>
              <Icon size={18} /><span>{label}</span>
            </button>
          ))}
        </nav>
        <div className="ops-user"><span>{user.username} · {ROLE_LABELS[user.role]}</span><button type="button" title="退出登录" onClick={onLogout}><LogOut size={18} /></button></div>
      </aside>
      <section className="ops-main">
        <header className="ops-topbar"><div><h1>明景内容运营助手</h1><p>{currentLabel}</p></div></header>
        <div className="ops-content">{children}</div>
      </section>
    </main>
  );
}
