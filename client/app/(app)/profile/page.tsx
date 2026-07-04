"use client";

import { useState } from "react";

import type { RewardEntry, User } from "@/lib/types";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useRewards } from "@/hooks/use-rewards";
import { useAuthModal } from "@/components/auth/auth-modal";
import { Button } from "@/components/ui/button";

export default function ProfilePage() {
  const { data: user, isLoading } = useCurrentUser();
  const authModal = useAuthModal();

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl space-y-4">
        <div className="h-24 animate-pulse rounded-xl bg-surface-2" />
        <div className="h-40 animate-pulse rounded-xl bg-surface-2" />
      </div>
    );
  }

  if (!user) {
    return (
      <div className="mx-auto max-w-2xl rounded-xl border border-border bg-surface-2 p-8 text-center">
        <p className="text-sm text-muted-foreground">Sign in to see your profile and rewards.</p>
        <Button className="mt-3" onClick={() => authModal.open("login")}>
          Sign in
        </Button>
      </div>
    );
  }

  return <ProfileContent user={user} />;
}

function ProfileContent({ user }: { user: User }) {
  const [page, setPage] = useState(1);
  const rewards = useRewards(page);

  const joined = new Date(user.created_at).toLocaleDateString(undefined, {
    month: "short",
    year: "numeric",
  });

  return (
    <div className="mx-auto max-w-2xl space-y-8">
      {/* Header + points */}
      <header className="flex items-center gap-4 rounded-xl border border-border bg-surface-2 p-5">
        <div className="grid size-16 shrink-0 place-items-center rounded-full bg-surface-3 text-lg font-semibold">
          {user.username.slice(0, 2).toUpperCase()}
        </div>
        <div className="min-w-0 flex-1">
          <h1 className="text-xl font-semibold">{user.username}</h1>
          <p className="font-mono text-xs text-subtle">
            {user.role} · joined {joined}
          </p>
        </div>
        <div className="text-right">
          <p className="stat text-gradient-reward text-3xl font-bold">
            {rewards.data ? rewards.data.total_points.toLocaleString() : "—"}
          </p>
          <p className="text-xs text-subtle">total points</p>
        </div>
      </header>

      {/* Badges */}
      <section className="space-y-3">
        <h2 className="text-sm font-medium uppercase tracking-widest text-subtle">Badges earned</h2>
        {rewards.isLoading ? (
          <div className="h-10 animate-pulse rounded-lg bg-surface-2" />
        ) : rewards.data && rewards.data.badges.length > 0 ? (
          <div className="flex flex-wrap gap-2">
            {rewards.data.badges.map((b) => (
              <span
                key={b.code}
                className="inline-flex items-center gap-1.5 rounded-full bg-reward/15 px-3 py-1 text-sm font-medium text-reward"
                title={`Earned ${new Date(b.awarded_at).toLocaleDateString()}`}
              >
                🏅 {b.label ?? b.code}
              </span>
            ))}
          </div>
        ) : (
          <p className="text-sm text-subtle">No badges yet — complete a badge challenge to earn one.</p>
        )}
      </section>

      {/* Reward history */}
      <section className="space-y-3">
        <h2 className="text-sm font-medium uppercase tracking-widest text-subtle">Reward history</h2>
        {rewards.isLoading ? (
          <LedgerSkeleton />
        ) : rewards.isError ? (
          <div className="flex items-center justify-between rounded-xl border border-border bg-surface-2 p-4">
            <span className="text-sm text-muted-foreground">Couldn&apos;t load your rewards.</span>
            <Button variant="outline" size="sm" onClick={() => rewards.refetch()}>
              Retry
            </Button>
          </div>
        ) : !rewards.data || rewards.data.data.length === 0 ? (
          <div className="rounded-xl border border-dashed border-border bg-surface-2/40 p-8 text-center text-sm text-muted-foreground">
            No rewards yet. Complete a challenge to earn your first.
          </div>
        ) : (
          <>
            <ul className="divide-y divide-border overflow-hidden rounded-xl border border-border bg-surface-2">
              {rewards.data.data.map((r) => (
                <RewardRow key={r.id} reward={r} />
              ))}
            </ul>
            {rewards.data.meta.pages > 1 && (
              <div className="flex items-center justify-center gap-3">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                  Prev
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {rewards.data.meta.page} of {rewards.data.meta.pages}
                </span>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= rewards.data.meta.pages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                </Button>
              </div>
            )}
          </>
        )}
      </section>
    </div>
  );
}

function RewardRow({ reward }: { reward: RewardEntry }) {
  const date = new Date(reward.created_at).toLocaleDateString(undefined, { month: "short", day: "numeric" });
  return (
    <li className="flex items-center gap-3 p-3">
      <span className="w-14 shrink-0 font-mono text-xs text-subtle">{date}</span>
      <span className="min-w-0 flex-1 truncate text-sm">
        {reward.reward_type === "badge" ? "Badge earned" : "Reward"} — {reward.challenge_name ?? "challenge"}
      </span>
      {reward.reward_type === "points" ? (
        <span className="stat text-sm font-semibold text-reward">+{reward.amount}</span>
      ) : (
        <span className="text-sm text-reward">🏅 {reward.label ?? reward.badge_code}</span>
      )}
    </li>
  );
}

function LedgerSkeleton() {
  return (
    <div className="space-y-px overflow-hidden rounded-xl border border-border bg-surface-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="h-12 animate-pulse bg-surface-3/40" />
      ))}
    </div>
  );
}
