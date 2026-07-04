/** Skeleton placeholder for the feed while posts load. No spinners (task rule). */
export function FeedSkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="rounded-xl border border-border bg-surface-2 p-4">
          <div className="flex gap-3">
            <div className="size-9 shrink-0 animate-pulse rounded-full bg-surface-3" />
            <div className="flex-1 space-y-2">
              <div className="h-4 w-3/4 animate-pulse rounded bg-surface-3" />
              <div className="h-3 w-full animate-pulse rounded bg-surface-3" />
              <div className="h-3 w-1/3 animate-pulse rounded bg-surface-3" />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
