import { useState, type FormEvent } from "react";
import { LockKeyhole } from "lucide-react";

export function LoginPage({ onLogin }: { onLogin: (username: string, password: string) => Promise<void> }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLoading(true);
    setError("");
    try {
      await onLogin(username, password);
    } catch (err) {
      setError(err instanceof Error ? err.message : "登录失败");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="login-page">
      <form className="login-panel" onSubmit={submit}>
        <div className="login-mark"><LockKeyhole size={22} /></div>
        <h1>明景内容运营助手</h1>
        <p>企业内容生成、审核与发布工作台</p>
        <label>账号<input autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} /></label>
        <label>密码<input type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
        <button className="primary-button" type="submit" disabled={loading || !username || !password}>{loading ? "登录中..." : "登录"}</button>
        {error ? <p className="error-message">{error}</p> : null}
      </form>
    </main>
  );
}
