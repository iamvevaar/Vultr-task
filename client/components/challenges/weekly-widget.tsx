"use client";

/**
 * Weekly Challenge widget — lives in the right rail, so it's present on every
 * app page (task: "persistent layout-level component on all 5 pages"). It polls
 * /challenges/weekly (30s) so progress updates live, and shows days until the
 * Monday reset. Progress is a Recharts ring (not a component progress bar).
 */

import { useWeeklyChallenge } from "@/hooks/use-challenges";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useAuthModal } from "@/components/auth/auth-modal";
import { ProgressRing } from "@/components/challenges/progress-ring";
import { Button } from "@/components/ui/button";

function daysUntilMonday(): number {
  const day = new Date().getDay(); // 0 Sun … 6 Sat
  const left = (1 - day + 7) % 7; // days to next Monday
  return left === 0 ? 7 : left; // today is Monday → resets in 7
}

function Shell({ children }: { children: React.ReactNode }) {
  return <div className="rounded-xl bg-surface-2 p-4">{children}</div>;
}

export function WeeklyWidget() {
  const { data: user, isLoading } = useCurrentUser();
  const authModal = useAuthModal();

  if (isLoading) {
    return (
      <Shell>
        <div className="h-20 animate-pulse rounded bg-surface-3" />
      </Shell>
    );
  }

  if (!user) {
    return (
      <Shell>
        <p className="text-xs font-medium uppercase tracking-widest text-subtle">Weekly Challenge</p>
        <p className="mt-2 text-sm text-muted-foreground">
          Sign in to join this week&apos;s challenge and earn points.
        </p>
        <Button size="sm" className="mt-3 w-full" onClick={() => authModal.open("login")}>
          Sign in
        </Button>
      </Shell>
    );
  }

  return <MemberWeekly />;
}

/** Only mounted when logged in → the polled query never fires for guests. */
function MemberWeekly() {
  const { data, isLoading, isError, refetch } = useWeeklyChallenge();

  if (isLoading) {
    return (
      <Shell>
        <div className="h-20 animate-pulse rounded bg-surface-3" />
      </Shell>
    );
  }

  if (isError) {
    return (
      <Shell>
        <p className="text-xs font-medium uppercase tracking-widest text-subtle">Weekly Challenge</p>
        <p className="mt-2 text-sm text-muted-foreground">Couldn&apos;t load it.</p>
        <Button variant="outline" size="sm" className="mt-3 w-full" onClick={() => refetch()}>
          Retry
        </Button>
      </Shell>
    );
  }

  if (!data) {
    return (
      <Shell>
        <p className="text-xs font-medium uppercase tracking-widest text-subtle">Weekly Challenge</p>
        <p className="mt-2 text-sm text-muted-foreground">No weekly challenge running right now.</p>
      </Shell>
    );
  }

  const p = data.progress;
  const completed = p.state === "completed";

  return (
    <Shell>
      <p className="text-xs font-medium uppercase tracking-widest text-subtle">Weekly Challenge</p>
      <p className="mt-1 text-sm font-medium">{data.name}</p>

      <div className="mt-3 flex items-center gap-3">
        <div className="relative size-14 shrink-0">
          <ProgressRing percent={p.percent} size={56} tone={completed ? "reward" : "primary"} />
          <div className="absolute inset-0 grid place-items-center">
            <span className="stat text-xs font-semibold">
              {p.current_value}/{p.target}
            </span>
          </div>
        </div>
        <div className="min-w-0">
          {data.reward.type === "points" ? (
            <p>
              <span className="stat text-gradient-reward text-lg font-bold">+{data.reward.amount}</span>{" "}
              <span className="text-xs text-muted-foreground">pts</span>
            </p>
          ) : (
            <p className="text-sm text-reward">🏅 {data.reward.label ?? data.reward.code}</p>
          )}
          {completed && <p className="text-xs font-medium text-success">✓ Completed</p>}
        </div>
      </div>

      <p className="mt-3 text-xs text-subtle">Resets Monday · {daysUntilMonday()}d left</p>
    </Shell>
  );
}
