"use client";

import { useCurrentUser } from "@/hooks/use-current-user";
import { useChallenges, useStreaks, useWeeklyChallenge } from "@/hooks/use-challenges";
import { useAuthModal } from "@/components/auth/auth-modal";
import { ChallengeCard } from "@/components/challenges/challenge-card";
import { StreakHeatmap } from "@/components/challenges/streak-heatmap";
import { Button } from "@/components/ui/button";

export default function ChallengesPage() {
  const { data: user, isLoading } = useCurrentUser();
  const authModal = useAuthModal();

  if (isLoading) return <PageSkeleton />;

  // Challenges are per-user, so this page requires auth.
  if (!user) {
    return (
      <div className="mx-auto max-w-3xl rounded-xl border border-border bg-surface-2 p-8 text-center">
        <p className="text-sm text-muted-foreground">Sign in to see your challenges and progress.</p>
        <Button className="mt-3" onClick={() => authModal.open("login")}>
          Sign in
        </Button>
      </div>
    );
  }

  return <ChallengesContent />;
}

/** Only mounted for logged-in users, so its polled queries never fire for guests. */
function ChallengesContent() {
  const challenges = useChallenges();
  const streaks = useStreaks();
  const weekly = useWeeklyChallenge();

  return (
    <div className="mx-auto max-w-3xl space-y-10">
      <header>
        <h1 className="text-2xl font-semibold">Challenges &amp; Progress</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Progress updates automatically — evaluation runs in the background (auto-refreshes every 30s).
        </p>
      </header>

      {/* Active challenges */}
      <Section title="Active challenges">
        {challenges.isLoading ? (
          <CardGridSkeleton />
        ) : challenges.isError ? (
          <ErrorRow label="challenges" onRetry={() => challenges.refetch()} />
        ) : !challenges.data || challenges.data.length === 0 ? (
          <Empty>No active challenges right now.</Empty>
        ) : (
          <div className="grid gap-3 sm:grid-cols-2">
            {challenges.data.map((c) => (
              <ChallengeCard key={c.id} challenge={c} />
            ))}
          </div>
        )}
      </Section>

      {/* Streak */}
      <Section title="Contribution streak">
        {streaks.isLoading ? (
          <div className="h-28 animate-pulse rounded-xl bg-surface-2" />
        ) : streaks.isError ? (
          <ErrorRow label="streaks" onRetry={() => streaks.refetch()} />
        ) : (
          <div className="rounded-xl border border-border bg-surface-2 p-4">
            <div className="mb-4 flex gap-6">
              {(() => {
                const commentStreak = streaks.data?.streaks.find((s) => s.event_type === "comment_posted");
                const best = Math.max(0, ...(streaks.data?.streaks.map((s) => s.longest_streak) ?? [0]));
                return (
                  <>
                    <Stat label="Current streak" value={commentStreak?.current_streak ?? 0} unit="days" />
                    <Stat label="Longest" value={best} unit="days" />
                  </>
                );
              })()}
            </div>
            <StreakHeatmap activity={streaks.data?.activity ?? []} />
          </div>
        )}
      </Section>

      {/* Weekly breakdown */}
      <Section title="This week">
        {weekly.isLoading ? (
          <div className="h-20 animate-pulse rounded-xl bg-surface-2" />
        ) : weekly.isError ? (
          <ErrorRow label="the weekly challenge" onRetry={() => weekly.refetch()} />
        ) : !weekly.data ? (
          <Empty>No weekly challenge running right now.</Empty>
        ) : (
          <div className="rounded-xl border border-border bg-surface-2 p-4">
            <ChallengeCard challenge={weekly.data} />
            <p className="mt-3 text-xs text-subtle">Resets Monday.</p>
          </div>
        )}
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-4">
      <h2 className="text-sm font-medium uppercase tracking-widest text-subtle">{title}</h2>
      {children}
    </section>
  );
}

function Stat({ label, value, unit }: { label: string; value: number; unit: string }) {
  return (
    <div>
      <p className="text-xs text-subtle">{label}</p>
      <p>
        <span className="stat text-gradient-reward text-2xl font-bold">{value}</span>{" "}
        <span className="text-xs text-muted-foreground">{unit}</span>
      </p>
    </div>
  );
}

function Empty({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-border bg-surface-2/40 p-8 text-center text-sm text-muted-foreground">
      {children}
    </div>
  );
}

function ErrorRow({ label, onRetry }: { label: string; onRetry: () => void }) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-border bg-surface-2 p-4">
      <span className="text-sm text-muted-foreground">Couldn&apos;t load {label}.</span>
      <Button variant="outline" size="sm" onClick={onRetry}>
        Retry
      </Button>
    </div>
  );
}

function CardGridSkeleton() {
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="h-28 animate-pulse rounded-xl bg-surface-2" />
      ))}
    </div>
  );
}

function PageSkeleton() {
  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div className="h-7 w-56 animate-pulse rounded bg-surface-3" />
      <CardGridSkeleton />
    </div>
  );
}
