export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://127.0.0.1:8000";

export async function readApiError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string };
    return data.detail ?? "请求失败";
  } catch {
    return response.text();
  }
}

export async function apiClient<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem("mingjing_access_token");
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  const response = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (response.status === 401) {
    localStorage.removeItem("mingjing_access_token");
    localStorage.removeItem("mingjing_user");
  }
  if (!response.ok) throw new Error(await readApiError(response));
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
