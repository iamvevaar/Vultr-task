"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";

import { cn } from "@/lib/utils";
import { usePosts, type Sort } from "@/hooks/use-posts";
import { Button } from "@/components/ui/button";
import { PostCard } from "./post-card";
import { FeedSkeleton } from "./feed-skeleton";
import type { PageMeta } from "@/lib/types";

const SORTS: Sort[] = ["latest", "trending"];

export function Feed() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  // Read state FROM the URL, so it's shareable and back/forward restores it.
  const sort: Sort = searchParams.get("sort") === "trending" ? "trending" : "latest";
  const page = Math.max(1, Number(searchParams.get("page")) || 1);

  const { data, isLoading, isError, refetch, isFetching } = usePosts({ sort, page });

  // Write state TO the URL (router.push adds a history entry → back nav works).
  const updateUrl = (next: { sort?: Sort; page?: number }) => {
    const params = new URLSearchParams(searchParams.toString());
    if (next.sort) {
      params.set("sort", next.sort);
      params.set("page", "1"); // changing sort resets to page 1
    }
    if (next.page) params.set("page", String(next.page));
    router.push(`${pathname}?${params.toString()}`);
  };

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-semibold">Developer Community</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Ask questions, share what you&apos;ve learned, and earn rewards.
      </p>

      {/* Tabs */}
      <div className="mt-5 flex gap-5 border-b border-border">
        {SORTS.map((s) => (
          <button
            key={s}
            onClick={() => updateUrl({ sort: s })}
            className={cn(
              "-mb-px border-b-2 pb-2 text-sm capitalize transition-colors",
              sort === s
                ? "border-primary font-medium text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground"
            )}
          >
            {s}
          </button>
        ))}
      </div>

      {/* List */}
      <div className="mt-6">
        {isLoading ? (
          <FeedSkeleton />
        ) : isError ? (
          <ErrorState onRetry={() => refetch()} />
        ) : !data || data.data.length === 0 ? (
          <EmptyState />
        ) : (
          <div className={cn("space-y-3 transition-opacity", isFetching && "opacity-60")}>
            {data.data.map((post) => (
              <PostCard key={post.id} post={post} />
            ))}
          </div>
        )}
      </div>

      {data && data.meta.pages > 1 && (
        <Pagination meta={data.meta} onPage={(p) => updateUrl({ page: p })} />
      )}
    </div>
  );
}

function Pagination({ meta, onPage }: { meta: PageMeta; onPage: (p: number) => void }) {
  return (
    <div className="mt-6 flex items-center justify-center gap-3">
      <Button variant="outline" size="sm" disabled={meta.page <= 1} onClick={() => onPage(meta.page - 1)}>
        Prev
      </Button>
      <span className="text-sm text-muted-foreground">
        Page {meta.page} of {meta.pages}
      </span>
      <Button variant="outline" size="sm" disabled={meta.page >= meta.pages} onClick={() => onPage(meta.page + 1)}>
        Next
      </Button>
    </div>
  );
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="rounded-xl bg-surface-2 p-8 text-center">
      <p className="text-sm text-muted-foreground">Couldn&apos;t load the feed.</p>
      <Button variant="outline" size="sm" className="mt-3" onClick={onRetry}>
        Retry
      </Button>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-xl bg-surface-2/40 p-10 text-center text-sm text-muted-foreground">
      No threads yet — be the first to post.
    </div>
  );
}
