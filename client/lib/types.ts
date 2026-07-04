/** Shared API types (mirror the backend's response schemas). */

export type Role = "user" | "admin";

export type User = {
  id: number;
  email: string;
  username: string;
  role: Role;
  created_at: string;
};

export type AuthResponse = {
  access_token: string; // present but unused by the browser (we rely on the cookie)
  token_type: string;
  user: User;
};
