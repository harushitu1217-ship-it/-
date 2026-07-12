import { useEffect, useMemo, useState } from "react";
import { Check, Clipboard, ExternalLink, RefreshCw, Send } from "lucide-react";
import { apiClient } from "../../lib/apiClient";

type PublishTask = {
  id: string;
  content_version_id: string;
  platform: string;
  mode: string;
  status: string;
  scheduled_at: string | null;
  retry_count: number;
  external_id: string | null;
  metrics: Record<string, number | string>;
};

type PublishPackage = {
  task_id: string;
  platform: string;
  title: string;
  body: string;
  tags: string[];
  keywords: string[];
  image_suggestions: string[];
  publish_tip: string;
  publish_url: string;
};

const PLATFORM_LABELS: Record<string, string> = {
  xiaohongshu: "小红书", douyin: "抖音", kuaishou: "快手", toutiao: "今日头条", shipinhao: "视频号", wechat: "公众号",
};
const STATUS_LABELS: Record<string, string> = {
  queued: "等待发布", published: "已发布", failed: "发布失败", ready_for_manual_publish: "待人工发布",
};

export function PublishingWorkspacePage() {
  const [tasks, setTasks] = useState<PublishTask[]>([]);
  const [selectedPackage, setSelectedPackage] = useState<PublishPackage | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function loadTasks() {
    setLoading(true);
    setError("");
    try {
      const data = await apiClient<{ items: PublishTask[] }>("/api/publish-tasks");
      setTasks(data.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : "发布任务加载失败");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { void loadTasks(); }, []);
  const automaticTasks = useMemo(() => tasks.filter((task) => task.mode !== "manual"), [tasks]);
  const manualTasks = useMemo(() => tasks.filter((task) => task.mode === "manual"), [tasks]);

  async function openPackage(taskId: string) {
    setSelectedPackage(await apiClient<PublishPackage>(`/api/publish-tasks/${taskId}/package`));
  }

  async function markPublished(taskId: string) {
    await apiClient(`/api/publish-tasks/${taskId}/mark-published`, { method: "POST" });
    setSelectedPackage(null);
    await loadTasks();
  }

  async function copyText(value: string) { await navigator.clipboard.writeText(value); }

  return (
    <section className="publishing-page">
      <header className="page-heading"><div><h2>发布任务</h2><p>审核通过的内容在这里进入自动发布或人工确认流程。</p></div><button type="button" className="icon-command" title="刷新任务" onClick={() => void loadTasks()}><RefreshCw size={18} /></button></header>
      {error ? <p className="error-message">{error}</p> : null}
      <div className="publishing-split">
        <section className="publish-lane automatic-lane">
          <div className="lane-heading"><div><Send size={19} /><h3>自动发布</h3></div><span>{automaticTasks.length} 个任务</span></div>
          <p className="lane-description">已获得官方授权的平台会在此排期、发布和重试。</p>
          {loading ? <p className="muted-text">正在加载...</p> : automaticTasks.length ? automaticTasks.map((task) => (
            <article className="publish-row" key={task.id}><div><strong>{PLATFORM_LABELS[task.platform] ?? task.platform}</strong><span>{STATUS_LABELS[task.status] ?? task.status}</span></div><small>重试 {task.retry_count}/3 {task.scheduled_at ? `· ${new Date(task.scheduled_at).toLocaleString()}` : ""}</small></article>
          )) : <div className="lane-empty"><strong>等待平台授权配置</strong><p>申请开放平台资质后，自动发布任务会直接出现在这里。</p></div>}
        </section>
        <section className="publish-lane manual-lane">
          <div className="lane-heading"><div><Clipboard size={19} /><h3>人工发布</h3></div><span>{manualTasks.length} 个任务</span></div>
          <p className="lane-description">复制文案、检查图片，然后打开官方创作者页面确认发布。</p>
          {loading ? <p className="muted-text">正在加载...</p> : manualTasks.length ? manualTasks.map((task) => (
            <article className="publish-row" key={task.id}><div><strong>{PLATFORM_LABELS[task.platform] ?? task.platform}</strong><span>{STATUS_LABELS[task.status] ?? task.status}</span></div><button type="button" className="secondary-button compact-button" onClick={() => void openPackage(task.id)}>打开人工发布包</button></article>
          )) : <div className="lane-empty"><strong>暂无待人工发布内容</strong><p>内容审核通过并创建发布任务后会显示在这里。</p></div>}
        </section>
      </div>
      {selectedPackage ? (
        <section className="publish-package" aria-label="人工发布包">
          <div className="package-heading"><div><span>{PLATFORM_LABELS[selectedPackage.platform]}</span><h3>{selectedPackage.title}</h3></div><a className="primary-button compact-button" href={selectedPackage.publish_url} target="_blank" rel="noreferrer"><ExternalLink size={16} />打开官方发布页</a></div>
          <div className="package-field"><div><strong>标题</strong><button type="button" title="复制标题" onClick={() => void copyText(selectedPackage.title)}><Clipboard size={16} /></button></div><p>{selectedPackage.title}</p></div>
          <div className="package-field"><div><strong>正文</strong><button type="button" title="复制正文" onClick={() => void copyText(selectedPackage.body)}><Clipboard size={16} /></button></div><p className="package-body">{selectedPackage.body}</p></div>
          <div className="package-tags">{selectedPackage.tags.map((tag) => <span key={tag}>#{tag}</span>)}</div>
          <div className="package-actions"><button type="button" className="secondary-button" onClick={() => setSelectedPackage(null)}>关闭</button><button type="button" className="primary-button" onClick={() => void markPublished(selectedPackage.task_id)}><Check size={17} />标记为已发布</button></div>
        </section>
      ) : null}
    </section>
  );
}
