"use client";

/**
 * Contribution-style streak heatmap: the last 14 weeks, one square per day,
 * shaded by how much activity that day had. Rows = weekday, columns = week.
 */

import type { ActivityDay } from "@/lib/types";

const WEEKS = 14;

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

function cellColor(count: number): string {
  if (count <= 0) return "var(--surface-3)";
  // graded gold: more activity → more opaque
  return `hsl(38 92% 58% / ${0.3 + Math.min(count, 4) * 0.17})`;
}

export function StreakHeatmap({ activity }: { activity: ActivityDay[] }) {
  // Count activity per day (an event on a day = one point of intensity).
  const counts = new Map<string, number>();
  for (const a of activity) counts.set(a.date, (counts.get(a.date) ?? 0) + 1);

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const total = WEEKS * 7;
  const start = new Date(today);
  start.setDate(start.getDate() - (total - 1));

  // Pad the first column so rows line up with weekdays (Sun = row 0).
  const cells: ({ date: string; count: number } | null)[] = [];
  for (let i = 0; i < start.getDay(); i++) cells.push(null);
  for (let i = 0; i < total; i++) {
    const d = new Date(start);
    d.setDate(d.getDate() + i);
    const key = isoDate(d);
    cells.push({ date: key, count: counts.get(key) ?? 0 });
  }

  return (
    <div>
      <div className="grid grid-flow-col grid-rows-7 gap-1">
        {cells.map((cell, i) =>
          cell === null ? (
            <div key={i} className="size-3" />
          ) : (
            <div
              key={i}
              title={`${cell.date}: ${cell.count} ${cell.count === 1 ? "action" : "actions"}`}
              className="size-3 rounded-[3px]"
              style={{ backgroundColor: cellColor(cell.count) }}
            />
          )
        )}
      </div>
      <div className="mt-3 flex items-center gap-1 text-xs text-subtle">
        <span>Less</span>
        {[0, 1, 2, 3].map((level) => (
          <div key={level} className="size-3 rounded-[3px]" style={{ backgroundColor: cellColor(level) }} />
        ))}
        <span>More</span>
      </div>
    </div>
  );
}
