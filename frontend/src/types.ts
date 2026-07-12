export type ContentType = "lead" | "education" | "product_intro";

export type CreationType =
  | "multiPlatform"
  | "xiaohongshu"
  | "douyin"
  | "kuaishou"
  | "toutiao"
  | "shipinhao"
  | "wechat";

export type Product = {
  name: string;
  aliases: string[];
  materials: string[];
  uses: string[];
  industries: string[];
  questions: string[];
};

export type ImageAsset = {
  id: string;
  url: string;
  original_name: string;
  content_type: string;
};

export type GeneratedContent = {
  platform: string;
  title: string;
  body: string;
  tags: string[];
  keywords: string[];
  image_suggestions: string[];
  image_assets: ImageAsset[];
  publish_tip: string;
  optional_script: string | null;
};

export type BootstrapData = {
  company: {
    name: string;
    summary: string;
    advantages: string[];
    industries: string[];
    contact_note: string;
    banned_phrases: string[];
  };
  products: Product[];
  publish_links: Record<string, string>;
};

export type AiConfigPublic = {
  configured: boolean;
  api_url: string;
  model: string;
  api_key_hint: string;
};

export type PlatformAuthConfigPublic = {
  platform: string;
  client_id: string;
  configured: boolean;
  client_secret_hint: string;
  redirect_uri: string;
  scopes: string[];
  auth_url_template: string;
  developer_portal_url: string;
  setup_steps: string[];
};

export type PlatformAuthStart = {
  platform: string;
  status: "ready" | "needs_config";
  authorize_url: string;
  qr_svg: string;
  callback_url: string;
  message: string;
  notes: string;
  developer_portal_url: string;
  setup_steps: string[];
};
