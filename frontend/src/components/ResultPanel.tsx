import { Copy, ExternalLink } from "lucide-react";
import { PLATFORMS } from "../data/platforms";
import type { GeneratedContent } from "../types";

const API_BASE = "http://127.0.0.1:8000";

function platformLabel(platform: string) {
  return PLATFORMS.find((item) => item.id === platform)?.label ?? platform;
}

export function ResultPanel({
  results,
  publishLinks,
}: {
  results: GeneratedContent[];
  publishLinks: Record<string, string>;
}) {
  if (!results.length) {
    return (
      <div className="empty-state">
        生成后会在这里看到六个平台的图文软文、关键词、标签和配图建议。
      </div>
    );
  }

  return (
    <section className="results" aria-label="生成结果">
      {results.map((item) => {
        const fullText = `${item.title}\n\n${item.body}\n\n标签：${item.tags.join(" ")}`;

        return (
          <article className="result-card" key={item.platform}>
            <div className="card-head">
              <h2>{platformLabel(item.platform)}</h2>
              <div className="actions">
                <button
                  type="button"
                  className="icon-button"
                  title="复制文案"
                  aria-label={`复制${platformLabel(item.platform)}文案`}
                  onClick={async () => {
                    await navigator.clipboard.writeText(fullText);
                  }}
                >
                  <Copy size={18} />
                </button>
                {publishLinks[item.platform] ? (
                  <a
                    className="icon-button link-button"
                    title="打开发布页"
                    aria-label={`打开${platformLabel(item.platform)}发布页`}
                    href={publishLinks[item.platform]}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <ExternalLink size={18} />
                  </a>
                ) : null}
              </div>
            </div>
            <h3>{item.title}</h3>
            <h4>文字内容</h4>
            <p className="body-text">{item.body}</p>
            <p>
              <strong>标签：</strong>
              {item.tags.join("、")}
            </p>
            <p>
              <strong>关键词：</strong>
              {item.keywords.slice(0, 8).join("、")}
            </p>
            <p>
              <strong>配图：</strong>
              {item.image_suggestions.join("、")}
            </p>
            {item.image_assets?.length ? (
              <section className="image-order" aria-label={`${platformLabel(item.platform)}图片上传顺序`}>
                <h4>图片上传顺序</h4>
                <ol>
                  {item.image_assets.map((asset) => (
                    <li key={asset.id}>
                      <span>{asset.original_name}</span>
                      <img src={`${API_BASE}${asset.url}`} alt={asset.original_name} />
                    </li>
                  ))}
                </ol>
              </section>
            ) : null}
            {item.optional_script ? (
              <p>
                <strong>口播：</strong>
                {item.optional_script}
              </p>
            ) : null}
            <p className="tip">{item.publish_tip}</p>
          </article>
        );
      })}
    </section>
  );
}
