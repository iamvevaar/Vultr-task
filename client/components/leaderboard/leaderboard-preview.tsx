"use client";

/** Compact top-3 leaderboard for the right rail. Links to the full page. */

import Link from "next/link";

import { useCurrentUser } from "@/hooks/use-current-user";
import { useLeaderboard } from "@/hooks/use-leaderboard";

const MEDALS = ["🥇", "🥈", "🥉"];

function Shell({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-border bg-surface-2 p-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-widest text-subtle">Top members</p>
        <Link href="/leaderboard" className="text-xs text-primary hover:underline">
          View all
        </Link>
      </div>
      {children}
    </div>
  );
}

export function LeaderboardPreview() {
  const { data: user } = useCurrentUser();
  // Leaderboard is auth-gated; only render the query for logged-in users.
  if (!user) {
    return (
      <div className="rounded-xl border border-border bg-surface-2 p-4">
        <p className="text-xs font-medium uppercase tracking-widest text-subtle">Top members</p>
        <p className="mt-2 text-sm text-muted-foreground">Sign in to see the leaderboard.</p>
      </div>
    );
  }
  return <PreviewList meId={user.id} />;
}

function PreviewList({ meId }: { meId: number }) {
  const lb = useLeaderboard(1, 3);

  if (lb.isLoading) {
    return (
      <Shell>
        <div className="mt-3 h-16 animate-pulse rounded bg-surface-3" />
      </Shell>
    );
  }
  if (lb.isError || !lb.data || lb.data.data.length === 0) {
    return (
      <Shell>
        <p className="mt-2 text-sm text-muted-foreground">No rankings yet.</p>
      </Shell>
    );
  }

  return (
    <Shell>
      <ul className="mt-3 space-y-2">
        {lb.data.data.map((entry) => (
          <li key={entry.user_id} className="flex items-center gap-2 text-sm">
            <span className="w-5 shrink-0 text-center">{MEDALS[entry.rank - 1] ?? entry.rank}</span>
            <span className="min-w-0 flex-1 truncate">
              {entry.username}
              {entry.user_id === meId && <span className="ml-1 text-xs text-primary">(you)</span>}
            </span>
            <span className="stat text-xs font-semibold text-reward">
              {entry.total_points.toLocaleString()}
            </span>
          </li>
        ))}
      </ul>
    </Shell>
  );
}
