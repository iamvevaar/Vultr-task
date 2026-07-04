/** Shared API types (mirror the backend's response schemas). */

export type Role = "user" | "admin";

export type User = {
  id: string;
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

export type Author = { id: string; username: string };

export type PostSummary = {
  id: string;
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
  id: string;
  body: string;
  author: Author;
  parent_comment_id: string | null;
  is_solution: boolean;
  created_at: string;
  replies: CommentNode[];
};

export type PostDetail = {
  id: string;
  title: string;
  body: string;
  author: Author;
  view_count: number;
  comment_count: number;
  created_at: string;
  solution_comment_id: string | null;
  comments: CommentNode[];
};

// --- Challenges, progress, streaks ---

export type Reward =
  | { type: "points"; amount: number }
  | { type: "badge"; code: string; label?: string };

export type ProgressInfo = {
  current_value: number;
  target: number;
  percent: number;
  state: "in_progress" | "completed";
  completed_at: string | null;
};

export type ChallengeWithProgress = {
  id: string;
  name: string;
  description: string;
  type: "count" | "streak";
  event_type: string;
  rule_config: Record<string, unknown>;
  reward: Reward;
  start_at: string;
  end_at: string;
  cadence: "one_off" | "weekly";
  status: string;
  progress: ProgressInfo;
};

export type StreakOut = {
  event_type: string;
  current_streak: number;
  longest_streak: number;
  last_active_date: string;
};

export type ActivityDay = { date: string; event_type: string };

export type StreaksResponse = { streaks: StreakOut[]; activity: ActivityDay[] };

// --- Rewards / profile ---

export type RewardEntry = {
  id: string;
  reward_type: "points" | "badge";
  amount: number;
  badge_code: string | null;
  label: string | null;
  source_challenge_id: string;
  challenge_name: string | null;
  created_at: string;
};

export type RewardBadge = { code: string; label: string | null; awarded_at: string };

export type RewardsPage = {
  data: RewardEntry[];
  meta: PageMeta;
  total_points: number;
  badges: RewardBadge[];
};

// --- Leaderboard ---

export type LeaderboardEntry = {
  rank: number;
  user_id: string;
  username: string;
  total_points: number;
};

export type LeaderboardPage = { data: LeaderboardEntry[]; meta: PageMeta };
