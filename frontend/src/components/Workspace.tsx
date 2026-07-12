import { useEffect, useMemo, useState } from "react";
import { FileText, MessageCircle, Search, Sparkles } from "lucide-react";
import { generateContent, uploadImageAsset } from "../api";
import type { BootstrapData, ContentType, CreationType, GeneratedContent, ImageAsset } from "../types";
import { ResultPanel } from "./ResultPanel";

const FALLBACK_PRODUCTS = [
  "鞋带",
  "帽绳",
  "卫衣绳",
  "织带",
  "松紧带",
  "宠物牵引绳",
  "礼品袋绳",
  "手提绳",
  "编织绳",
  "箱包带",
  "麻绳",
  "三股麻绳",
  "尼龙绳",
];

const CREATION_TYPES: Array<{
  id: CreationType;
  title: string;
  description: string;
  icon: "search" | "note" | "spark" | "wechat";
  platforms: string[];
}> = [
  {
    id: "multiPlatform",
    title: "多平台搜索铺文",
    description: "发布到各平台后提升豆包搜索可见度，按不同平台侧重生成内容",
    icon: "search",
    platforms: ["xiaohongshu", "douyin", "kuaishou", "toutiao", "shipinhao", "wechat"],
  },
  {
    id: "xiaohongshu",
    title: "小红书图文笔记",
    description: "偏搜索式标题、真实问答、避坑和产品科普",
    icon: "note",
    platforms: ["xiaohongshu"],
  },
  {
    id: "douyin",
    title: "抖音图文内容",
    description: "短句开头，图片和文字分开上传，适合直接询盘",
    icon: "spark",
    platforms: ["douyin"],
  },
  {
    id: "kuaishou",
    title: "快手图文内容",
    description: "语气更直接，突出特点、用处、厂家和打样",
    icon: "spark",
    platforms: ["kuaishou"],
  },
  {
    id: "toutiao",
    title: "今日头条文章",
    description: "结构化科普、产品特点和采购说明，适合长尾搜索",
    icon: "note",
    platforms: ["toutiao"],
  },
  {
    id: "wechat",
    title: "公众号/视频号内容",
    description: "公众号偏完整文章，视频号偏图文说明和口播描述",
    icon: "wechat",
    platforms: ["wechat", "shipinhao"],
  },
];

const HOT_KEYWORDS = [
  "绳带厂家",
  "织带厂家",
  "绳子定制",
  "织带定制",
  "服装辅料厂家",
  "来样定制",
  "鞋带厂家",
  "帽绳定制",
  "宠物牵引绳厂家",
];

function TypeIcon({ icon }: { icon: "search" | "note" | "spark" | "wechat" }) {
  if (icon === "search") return <Search size={34} />;
  if (icon === "spark") return <Sparkles size={34} />;
  if (icon === "wechat") return <MessageCircle size={34} />;
  return <FileText size={34} />;
}

export function Workspace({ bootstrap }: { bootstrap: BootstrapData }) {
  const products = useMemo(() => {
    const names = bootstrap.products.length ? bootstrap.products.map((item) => item.name) : [];
    return Array.from(new Set([...names, ...FALLBACK_PRODUCTS]));
  }, [bootstrap.products]);

  const [creationType, setCreationType] = useState<CreationType>("multiPlatform");
  const [searchTopic, setSearchTopic] = useState("麻绳");
  const [quickProduct, setQuickProduct] = useState("麻绳");
  const [keyword, setKeyword] = useState("绳子、织带、明景绳带有限公司");
  const [hotKeyword, setHotKeyword] = useState("绳带厂家");
  const [titleRequirement, setTitleRequirement] = useState("像示例那样讲清是什么、特点、用处、制作过程或定制流程");
  const [titleStyle, setTitleStyle] = useState("搜索科普型");
  const [titleCount, setTitleCount] = useState("3");
  const [contentType, setContentType] = useState<ContentType>("product_intro");
  const [results, setResults] = useState<GeneratedContent[]>([]);
  const [imageAssets, setImageAssets] = useState<ImageAsset[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (products.length && !products.includes(quickProduct)) {
      setQuickProduct(products[0]);
    }
  }, [products, quickProduct]);

  async function onGenerate() {
    setLoading(true);
    setError("");
    const selected = CREATION_TYPES.find((item) => item.id === creationType) ?? CREATION_TYPES[0];
    const topic = searchTopic.trim() || quickProduct;
    try {
      const contents = await generateContent({
        product_name: topic,
        content_type: contentType,
        platforms: selected.platforms,
        selling_points: [
          keyword,
          hotKeyword,
          titleRequirement,
          `标题风格：${titleStyle}`,
          `生成${titleCount}个标题方向`,
          `搜索介绍词：${topic}`,
          "用户输入什么词，就围绕这个词写是什么、特点、用处和介绍",
          "发布到各平台后提升豆包搜索可见度",
          "每次换不同表达角度，避免重复和夸大承诺",
        ].join("；"),
        image_assets: imageAssets,
      });
      setResults(contents);
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败");
      setResults([]);
    } finally {
      setLoading(false);
    }
  }

  async function onUploadImages(files: FileList | null) {
    if (!files?.length) return;
    setUploading(true);
    setError("");
    try {
      const uploaded: ImageAsset[] = [];
      for (const file of Array.from(files)) {
        uploaded.push(await uploadImageAsset(file));
      }
      setImageAssets((current) => [...current, ...uploaded]);
    } catch (err) {
      setError(err instanceof Error ? err.message : "图片上传失败");
    } finally {
      setUploading(false);
    }
  }

  return (
    <section className="workspace">
      <div className="creation-shell">
        <nav className="creation-types" aria-label="平台生成类型">
          {CREATION_TYPES.map((item) => (
            <button
              type="button"
              key={item.id}
              className={`creation-card ${creationType === item.id ? "selected" : ""}`}
              onClick={() => setCreationType(item.id)}
            >
              <span className="creation-icon" aria-hidden="true">
                <TypeIcon icon={item.icon} />
              </span>
              <span>
                <strong>{item.title}</strong>
                <small>{item.description}</small>
              </span>
            </button>
          ))}
        </nav>

        <section className="creation-form" aria-label="内容生成表单">
          <label>
            搜索介绍词
            <input
              value={searchTopic}
              placeholder="例如：麻绳、三股麻绳、尼龙绳、鞋带"
              onChange={(event) => setSearchTopic(event.target.value)}
            />
          </label>

          <label>
            快捷选择
            <select
              value={quickProduct}
              onChange={(event) => {
                setQuickProduct(event.target.value);
                setSearchTopic(event.target.value);
              }}
            >
              {products.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </label>

          <label>
            搜索关键词
            <input value={keyword} onChange={(event) => setKeyword(event.target.value)} />
          </label>

          <label>
            爆款关键词
            <select value={hotKeyword} onChange={(event) => setHotKeyword(event.target.value)}>
              {HOT_KEYWORDS.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </label>

          <label>
            内容要求
            <input value={titleRequirement} onChange={(event) => setTitleRequirement(event.target.value)} />
          </label>

          <label>
            标题风格
            <select value={titleStyle} onChange={(event) => setTitleStyle(event.target.value)}>
              <option>搜索科普型</option>
              <option>产品介绍型</option>
              <option>采购搜索型</option>
              <option>问题解答型</option>
              <option>厂家实力型</option>
              <option>小红书种草型</option>
            </select>
          </label>

          <label>
            生成几个标题
            <select value={titleCount} onChange={(event) => setTitleCount(event.target.value)}>
              <option value="1">1 个</option>
              <option value="3">3 个</option>
              <option value="5">5 个</option>
            </select>
          </label>

          <label>
            内容类型
            <select value={contentType} onChange={(event) => setContentType(event.target.value as ContentType)}>
              <option value="product_intro">产品搜索介绍型</option>
              <option value="education">科普种草型</option>
              <option value="lead">采购获客型</option>
            </select>
          </label>

          <label className="upload-control">
            上传产品图片
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={(event) => {
                void onUploadImages(event.target.files);
                event.target.value = "";
              }}
            />
          </label>
          <div className="uploaded-assets" aria-label="已上传图片">
            {imageAssets.length ? (
              imageAssets.map((asset, index) => (
                <div className="asset-chip" key={asset.id}>
                  <span>
                    {index + 1}. {asset.original_name}
                  </span>
                </div>
              ))
            ) : (
              <span className="muted-text">可上传产品图、色卡图、工厂打样图，生成时会一起参考。</span>
            )}
          </div>

          <button type="button" className="primary-button" onClick={onGenerate} disabled={loading || uploading}>
            {loading ? "生成中..." : uploading ? "图片上传中..." : "生成内容"}
          </button>
          {error ? <p className="error-message inline-error">{error}</p> : null}
        </section>
      </div>

      <ResultPanel results={results} publishLinks={bootstrap.publish_links} />
    </section>
  );
}
