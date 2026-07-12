import { useState } from "react";
import { startPlatformAuth } from "../api";
import { PLATFORM_PUBLISH_REQUIREMENTS, PLATFORM_STRATEGIES, TOPIC_LIBRARY } from "../data/contentStrategy";
import type { PlatformAuthStart } from "../types";

export function TopicLibraryPage() {
  return (
    <section className="page-panel" aria-label="话题库页面">
      <div className="page-heading">
        <div>
          <h2>话题库</h2>
          <p>先内置一批适合绳带厂的搜索话题，后续可以继续接入网上热点更新。</p>
        </div>
      </div>
      <div className="topic-grid">
        {TOPIC_LIBRARY.map((item) => (
          <article className="topic-card" key={item.topic}>
            <div className="topic-head">
              <h3>{item.topic}</h3>
              <div className="topic-badges">
                <span>爆款话题</span>
                <span>热度：{item.heatLevel}</span>
              </div>
            </div>
            <p>{item.angle}</p>
            <p>
              <strong>内容意图：</strong>
              {item.intent}
            </p>
            <p>
              <strong>适合平台：</strong>
              {item.platforms.join("、")}
            </p>
            <div className="topic-detail">
              <strong>标题方向</strong>
              <ul>
                {item.titleHooks.map((hook) => (
                  <li key={hook}>{hook}</li>
                ))}
              </ul>
            </div>
            <p>
              <strong>内容侧重：</strong>
              {item.publishAngles.join("、")}
            </p>
            <p>
              <strong>素材需求：</strong>
              {item.materialsNeeded.join("、")}
            </p>
            <p>
              <strong>发布建议：</strong>
              {item.publishSuggestion}
            </p>
            <p className="prep-note">{item.automationReady}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function PlatformTemplatePage() {
  return (
    <section className="page-panel" aria-label="平台模板页面">
      <div className="page-heading">
        <div>
          <h2>平台模板</h2>
          <p>每个平台的标题、排版和内容侧重点不同，生成时会按这些方向组织软文。</p>
        </div>
      </div>
      <div className="strategy-grid">
        {PLATFORM_STRATEGIES.map((item) => (
          <article className="strategy-card" key={item.id}>
            <h3>{item.name}</h3>
            <p className="strategy-focus">{item.focus}</p>
            <div>
              <strong>标题模板</strong>
              <ul>
                {item.titlePatterns.map((pattern) => (
                  <li key={pattern}>{pattern}</li>
                ))}
              </ul>
            </div>
            <div>
              <strong>排版结构</strong>
              <p>{item.layout.join(" / ")}</p>
            </div>
            <div>
              <strong>相关话题</strong>
              <p>{item.topics.join("、")}</p>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export function PublishPrepPage() {
  const [authResult, setAuthResult] = useState<PlatformAuthStart | null>(null);
  const [authError, setAuthError] = useState("");

  async function onStartAuth(platform: string) {
    setAuthError("");
    try {
      setAuthResult(await startPlatformAuth(platform));
    } catch (err) {
      setAuthError(err instanceof Error ? err.message : "扫码授权启动失败");
    }
  }

  return (
    <section className="page-panel" aria-label="自动上传准备页面">
      <div className="page-heading">
        <div>
          <h2>自动上传准备</h2>
          <p>这一页先把下一版自动发布需要的授权、图片、文案字段和话题标签整理好，后续接平台 API 时直接复用。</p>
        </div>
      </div>
      <div className="publish-prep-grid">
        {PLATFORM_PUBLISH_REQUIREMENTS.map((item) => (
          <article className="publish-prep-card" key={item.id}>
            <div className="publish-prep-head">
              <h3>{item.name}</h3>
              <span>{item.authStatus}</span>
            </div>
            <dl>
              <div>
                <dt>授权状态</dt>
                <dd>{item.authStatus}</dd>
              </div>
              <div>
                <dt>图片上传</dt>
                <dd>{item.imageUpload}</dd>
              </div>
              <div>
                <dt>文案字段</dt>
                <dd>{item.copyFields}</dd>
              </div>
              <div>
                <dt>话题标签</dt>
                <dd>{item.topicTags.join("、")}</dd>
              </div>
              <div>
                <dt>发布入口</dt>
                <dd>{item.publishEntry}</dd>
              </div>
            </dl>
            <button type="button" className="secondary-button auth-button" onClick={() => void onStartAuth(item.id)}>
              {item.name}扫码授权
            </button>
            <a className="portal-link" href={item.developerPortalUrl} target="_blank" rel="noreferrer">
              去开放平台申请
            </a>
          </article>
        ))}
      </div>
      {authError ? <p className="error-message inline-error">{authError}</p> : null}
      {authResult ? (
        <section className="auth-result" aria-label="扫码授权结果">
          <div>
            <strong>{authResult.status === "ready" ? "扫码授权二维码" : "需要先配置开放平台应用"}</strong>
            <p>{authResult.message}</p>
            <p>{authResult.notes}</p>
            {authResult.authorize_url ? (
              <a href={authResult.authorize_url} target="_blank" rel="noreferrer">
                打开授权链接
              </a>
            ) : null}
            {authResult.developer_portal_url ? (
              <a href={authResult.developer_portal_url} target="_blank" rel="noreferrer">
                去官方开放平台
              </a>
            ) : null}
            {authResult.setup_steps.length ? (
              <ol>
                {authResult.setup_steps.map((step) => (
                  <li key={step}>{step}</li>
                ))}
              </ol>
            ) : null}
          </div>
          {authResult.qr_svg ? <img src={authResult.qr_svg} alt="平台扫码授权二维码" /> : null}
        </section>
      ) : null}
    </section>
  );
}
