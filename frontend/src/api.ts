import type {
  AiConfigPublic,
  BootstrapData,
  ContentType,
  GeneratedContent,
  ImageAsset,
  PlatformAuthConfigPublic,
  PlatformAuthStart,
} from "./types";

const API_BASE = "http://127.0.0.1:8000";

export async function fetchBootstrap(): Promise<BootstrapData> {
  const response = await fetch(`${API_BASE}/api/bootstrap`);
  if (!response.ok) {
    throw new Error("资料库加载失败");
  }
  return response.json();
}

async function readError(response: Response): Promise<string> {
  try {
    const data = (await response.json()) as { detail?: string };
    return data.detail ?? "请求失败";
  } catch {
    return response.text();
  }
}

export async function fetchAiConfig(): Promise<AiConfigPublic> {
  const response = await fetch(`${API_BASE}/api/ai-config`);
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json();
}

export async function saveAiConfig(input: {
  api_url: string;
  api_key: string;
  model: string;
}): Promise<AiConfigPublic> {
  const response = await fetch(`${API_BASE}/api/ai-config`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json();
}

export async function uploadImageAsset(file: File): Promise<ImageAsset> {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch(`${API_BASE}/api/assets/images`, {
    method: "POST",
    body: formData,
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json();
}

export async function generateContent(input: {
  product_name: string;
  content_type: ContentType;
  platforms: string[];
  selling_points: string;
  image_assets: ImageAsset[];
}): Promise<GeneratedContent[]> {
  const response = await fetch(`${API_BASE}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const data = (await response.json()) as { contents?: GeneratedContent[] };
  return data.contents ?? [];
}

export async function fetchPlatformAuthConfigs(): Promise<PlatformAuthConfigPublic[]> {
  const response = await fetch(`${API_BASE}/api/platform-auth/configs`);
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  const data = (await response.json()) as { items?: PlatformAuthConfigPublic[] };
  return data.items ?? [];
}

export async function savePlatformAuthConfig(input: {
  platform: string;
  client_id: string;
  client_secret: string;
  redirect_uri: string;
  scopes: string[];
  auth_url_template?: string;
}): Promise<PlatformAuthConfigPublic> {
  const response = await fetch(`${API_BASE}/api/platform-auth/configs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json();
}

export async function startPlatformAuth(platform: string): Promise<PlatformAuthStart> {
  const response = await fetch(`${API_BASE}/api/platform-auth/${platform}/start`, {
    method: "POST",
  });
  if (!response.ok) {
    throw new Error(await readError(response));
  }
  return response.json();
}
