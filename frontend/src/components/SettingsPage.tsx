import { useEffect, useState } from "react";
import { Settings } from "lucide-react";
import { fetchAiConfig, fetchPlatformAuthConfigs, saveAiConfig, savePlatformAuthConfig } from "../api";
import type { AiConfigPublic, PlatformAuthConfigPublic } from "../types";

const PLATFORM_OPTIONS = [
  { id: "xiaohongshu", name: "小红书" },
  { id: "douyin", name: "抖音图文" },
  { id: "kuaishou", name: "快手图文" },
  { id: "toutiao", name: "今日头条" },
  { id: "shipinhao", name: "视频号" },
  { id: "wechat", name: "公众号" },
];

export function SettingsPage() {
  const [config, setConfig] = useState<AiConfigPublic>({
    configured: false,
    api_url: "",
    model: "",
    api_key_hint: "",
  });
  const [apiUrl, setApiUrl] = useState("");
  const [apiKey, setApiKey] = useState("");
  const [model, setModel] = useState("");
  const [message, setMessage] = useState("");
  const [authConfigs, setAuthConfigs] = useState<PlatformAuthConfigPublic[]>([]);
  const [authPlatform, setAuthPlatform] = useState("douyin");
  const [clientId, setClientId] = useState("");
  const [clientSecret, setClientSecret] = useState("");
  const [redirectUri, setRedirectUri] = useState("http://127.0.0.1:8000/api/platform-auth/douyin/callback");
  const [scopes, setScopes] = useState("user_info,video.create");
  const [authMessage, setAuthMessage] = useState("");

  useEffect(() => {
    let active = true;
    fetchAiConfig()
      .then((data) => {
        if (!active) return;
        setConfig(data);
        setApiUrl(data.api_url);
        setModel(data.model);
      })
      .catch(() => {
        if (active) {
          setMessage("后端连接后可保存 AI API 配置。");
        }
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;
    fetchPlatformAuthConfigs()
      .then((items) => {
        if (active) setAuthConfigs(items);
      })
      .catch(() => {
        if (active) setAuthMessage("后端连接后可保存平台扫码授权配置。");
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const current = authConfigs.find((item) => item.platform === authPlatform);
    setClientId(current?.client_id ?? "");
    setRedirectUri(current?.redirect_uri || `http://127.0.0.1:8000/api/platform-auth/${authPlatform}/callback`);
    setScopes((current?.scopes?.length ? current.scopes : ["user_info"]).join(","));
    setClientSecret("");
  }, [authConfigs, authPlatform]);

  async function onSaveConfig() {
    setMessage("");
    try {
      const saved = await saveAiConfig({
        api_url: apiUrl,
        api_key: apiKey,
        model,
      });
      setConfig(saved);
      setApiKey("");
      setMessage("AI API 已保存。");
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "AI API 保存失败");
    }
  }

  async function onSavePlatformAuthConfig() {
    setAuthMessage("");
    try {
      const saved = await savePlatformAuthConfig({
        platform: authPlatform,
        client_id: clientId,
        client_secret: clientSecret,
        redirect_uri: redirectUri,
        scopes: scopes
          .split(",")
          .map((item) => item.trim())
          .filter(Boolean),
      });
      setAuthConfigs((items) => {
        const next = items.filter((item) => item.platform !== saved.platform);
        return [...next, saved];
      });
      setClientSecret("");
      setAuthMessage("平台授权配置已保存，密钥不会在页面明文显示。");
    } catch (err) {
      setAuthMessage(err instanceof Error ? err.message : "平台授权配置保存失败");
    }
  }

  return (
    <section className="page-panel settings-page" aria-label="设置页面">
      <div className="page-heading">
        <Settings size={22} />
        <div>
          <h2>设置</h2>
          <p>API 接口、模型名称和后续系统参数都放在这里，创作页面只负责生成内容。</p>
        </div>
      </div>

      <section className="settings-card" aria-label="AI API 设置">
        <div className="settings-title">
          <strong>AI API 设置</strong>
          <span>{config.configured ? "已配置" : "未配置"}</span>
        </div>
        <div className="settings-grid">
          <label>
            API 地址
            <input
              value={apiUrl}
              onChange={(event) => setApiUrl(event.target.value)}
              placeholder="DeepSeek 填 https://api.deepseek.com，系统会自动补全调用路径"
            />
          </label>
          <label>
            API Key
            <input
              type="password"
              value={apiKey}
              onChange={(event) => setApiKey(event.target.value)}
              placeholder={config.api_key_hint || "粘贴你的 API Key"}
            />
          </label>
          <label>
            模型名称
            <input value={model} onChange={(event) => setModel(event.target.value)} placeholder="例如 gpt-4.1-mini" />
          </label>
        </div>
        <button type="button" className="primary-button compact-button" onClick={onSaveConfig}>
          保存 API 配置
        </button>
        {message ? <p className="settings-message">{message}</p> : null}
      </section>

      <section className="settings-card auth-settings-card" aria-label="平台扫码授权设置">
        <div className="settings-title">
          <strong>平台扫码授权</strong>
          <span>{authConfigs.filter((item) => item.configured).length} 个平台已配置</span>
        </div>
        <div className="settings-grid">
          <label>
            选择平台
            <select value={authPlatform} onChange={(event) => setAuthPlatform(event.target.value)}>
              {PLATFORM_OPTIONS.map((item) => (
                <option value={item.id} key={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          <label>
            App ID / Client ID
            <input value={clientId} onChange={(event) => setClientId(event.target.value)} placeholder="开放平台应用 ID" />
          </label>
          <label>
            App Secret
            <input
              type="password"
              value={clientSecret}
              onChange={(event) => setClientSecret(event.target.value)}
              placeholder="开放平台应用密钥，保存后不再明文显示"
            />
          </label>
          <label>
            回调地址
            <input value={redirectUri} onChange={(event) => setRedirectUri(event.target.value)} />
          </label>
          <label>
            权限范围
            <input value={scopes} onChange={(event) => setScopes(event.target.value)} placeholder="多个权限用英文逗号分隔" />
          </label>
        </div>
        <button type="button" className="primary-button compact-button" onClick={onSavePlatformAuthConfig}>
          保存平台授权配置
        </button>
        {authMessage ? <p className="settings-message">{authMessage}</p> : null}
      </section>
    </section>
  );
}
