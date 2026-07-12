export type AuthUser = {
  id: string;
  username: string;
  role: "admin" | "operator" | "reviewer";
  is_active: boolean;
};
