"use client";

/**
 * A radial progress ring rendered with Recharts (RadialBarChart).
 * This is the task's required data-viz "via a charting library" — the allowed
 * "challenge progress rings" option. (A CSS/component progress bar would NOT
 * satisfy the requirement.)
 */

import { PolarAngleAxis, RadialBar, RadialBarChart } from "recharts";

export function ProgressRing({
  percent,
  tone = "primary",
  size = 72,
}: {
  percent: number;
  tone?: "primary" | "reward";
  size?: number;
}) {
  const color = tone === "reward" ? "hsl(38 92% 58%)" : "hsl(212 100% 60%)";
  const data = [{ value: Math.max(0, Math.min(100, percent)) }];

  return (
    <RadialBarChart
      width={size}
      height={size}
      data={data}
      innerRadius="72%"
      outerRadius="100%"
      startAngle={90}
      endAngle={-270}
    >
      {/* Maps value 0..100 onto the arc sweep. */}
      <PolarAngleAxis type="number" domain={[0, 100]} tick={false} />
      <RadialBar
        background={{ fill: "var(--surface-3)" }} /* the track = surface-3 (follows the theme) */
        dataKey="value"
        cornerRadius={10}
        fill={color}
      />
    </RadialBarChart>
  );
}
