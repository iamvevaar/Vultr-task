"use client";

import { useState } from "react";

import { cn } from "@/lib/utils";
import type { LeaderboardEntry } from "@/lib/types";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useLeaderboard } from "@/hooks/use-leaderboard";
import { useAuthModal } from "@/components/auth/auth-modal";
import { Button } from "@/components/ui/button";

const MEDALS = ["🥇", "🥈", "🥉"];

export default function LeaderboardPage() {
  const { data: user, isLoading } = useCurrentUser();
  const authModal = useAuthModal();

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl space-y-3">
        <div className="h-7 w-40 animate-pulse rounded bg-surface-3" />
        <div className="h-64 animate-pulse rounded-xl bg-surface-2" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-2xl rounded-xl border border-border bg-surface-2 p-8 text-center">
        <p className="text-sm text-muted-foreground">Sign in to see the leaderboard.</p>
        <Button className="mt-3" onClick={() => authModal.open("login")}>
          Sign in
        </Button>
      </div>
    );
  }

  return <LeaderboardContent meId={user.id} />;
}

function LeaderboardContent({ meId }: { meId: number }) {
  const [page, setPage] = useState(1);
  const lb = useLeaderboard(page);

  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <header>
        <h1 className="text-2xl font-semibold">Leaderboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">Ranked by total points earned.</p>
      </header>

      {lb.isLoading ? (
        <div className="h-64 animate-pulse rounded-xl bg-surface-2" />
      ) : lb.isError ? (
        <div className="flex items-center justify-between rounded-xl border border-border bg-surface-2 p-4">
          <span className="text-sm text-muted-foreground">Couldn&apos;t load the leaderboard.</span>
          <Button variant="outline" size="sm" onClick={() => lb.refetch()}>
            Retry
          </Button>
        </div>
      ) : !lb.data || lb.data.data.length === 0 ? (
        <div className="rounded-xl border border-dashed border-border bg-surface-2/40 p-8 text-center text-sm text-muted-foreground">
          No ranked members yet.
        </div>
      ) : (
        <>
          <ul className="divide-y divide-border overflow-hidden rounded-xl border border-border bg-surface-2">
            {lb.data.data.map((entry) => (
              <Row key={entry.user_id} entry={entry} isMe={entry.user_id === meId} />
            ))}
          </ul>
          {lb.data.meta.pages > 1 && (
            <div className="flex items-center justify-center gap-3">
              <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                Prev
              </Button>
              <span className="text-sm text-muted-foreground">
                Page {lb.data.meta.page} of {lb.data.meta.pages}
              </span>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= lb.data.meta.pages}
                onClick={() => setPage((p) => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Row({ entry, isMe }: { entry: LeaderboardEntry; isMe: boolean }) {
  const medal = entry.rank <= 3 ? MEDALS[entry.rank - 1] : null;
  return (
    <li className={cn("flex items-center gap-3 p-3", isMe && "bg-primary/10")}>
      <span className="w-8 shrink-0 text-center font-mono text-sm text-muted-foreground">
        {medal ?? `#${entry.rank}`}
      </span>
      <div className="grid size-8 shrink-0 place-items-center rounded-full bg-surface-3 text-xs font-medium">
        {entry.username.slice(0, 2).toUpperCase()}
      </div>
      <span className="min-w-0 flex-1 truncate text-sm font-medium">
        {entry.username}
        {isMe && <span className="ml-2 rounded bg-primary/20 px-1.5 py-0.5 text-xs text-primary">You</span>}
      </span>
      <span className="stat text-sm font-semibold text-reward">{entry.total_points.toLocaleString()}</span>
    </li>
  );
}
