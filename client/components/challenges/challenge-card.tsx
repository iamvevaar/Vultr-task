import { cn } from "@/lib/utils";
import type { ChallengeWithProgress, Reward } from "@/lib/types";
import { ProgressRing } from "./progress-ring";

export function ChallengeCard({ challenge }: { challenge: ChallengeWithProgress }) {
  const completed = challenge.progress.state === "completed";

  return (
    <div className="rounded-xl bg-surface-2 p-4">
      <div className="flex items-center gap-4">
        <div className="relative size-[72px] shrink-0">
          <ProgressRing percent={challenge.progress.percent} tone={completed ? "reward" : "primary"} />
          <div className="absolute inset-0 grid place-items-center">
            <span className="stat text-sm font-semibold">
              {challenge.progress.current_value}/{challenge.progress.target}
            </span>
          </div>
        </div>

        <div className="min-w-0 flex-1">
          <p className="font-medium leading-snug">{challenge.name}</p>
          {challenge.description && (
            <p className="mt-0.5 line-clamp-2 text-xs text-muted-foreground">{challenge.description}</p>
          )}
          <div className="mt-2 flex items-center gap-2">
            <RewardBadge reward={challenge.reward} completed={completed} />
            {completed && <span className="text-xs font-medium text-success">✓ Completed</span>}
          </div>
        </div>
      </div>
    </div>
  );
}

function RewardBadge({ reward, completed }: { reward: Reward; completed: boolean }) {
  if (reward.type === "points") {
    return (
      <span
        className={cn(
          "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold",
          completed ? "fill-reward" : "bg-reward/15 text-reward"
        )}
      >
        <span className="stat">+{reward.amount}</span> pts
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 rounded-full bg-reward/15 px-2 py-0.5 text-xs font-medium text-reward">
      🏅 {reward.label ?? reward.code}
    </span>
  );
}
