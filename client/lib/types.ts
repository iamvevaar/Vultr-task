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

// --- Forum ---

export type Author = { id: number; username: string };

export type PostSummary = {
  id: number;
  title: string;
  body: string;
  author: Author;
  view_count: number;
  comment_count: number;
  created_at: string;
};

export type PageMeta = { page: number; limit: number; total: number; pages: number };

export type Paginated<T> = { data: T[]; meta: PageMeta };

// A comment plus its nested replies (the backend returns a tree).
export type CommentNode = {
  id: number;
  body: string;
  author: Author;
  parent_comment_id: number | null;
  is_solution: boolean;
  created_at: string;
  replies: CommentNode[];
};

export type PostDetail = {
  id: number;
  title: string;
  body: string;
  author: Author;
  view_count: number;
  comment_count: number;
  created_at: string;
  solution_comment_id: number | null;
  comments: CommentNode[];
};
