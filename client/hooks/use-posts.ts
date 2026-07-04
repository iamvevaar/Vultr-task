/**
 * usePosts — fetch a page of the feed. Single responsibility: given sort + page,
 * return the paginated posts. placeholderData keeps the previous page visible
 * while the next one loads, so pagination doesn't flash to a skeleton.
 */

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { Paginated, PostSummary } from "@/lib/types";

export type Sort = "latest" | "trending";

export function usePosts({ sort, page, limit = 10 }: { sort: Sort; page: number; limit?: number }) {
  return useQuery({
    queryKey: ["posts", sort, page, limit],
    queryFn: () =>
      apiFetch<Paginated<PostSummary>>(`/posts?sort=${sort}&page=${page}&limit=${limit}`),
    placeholderData: keepPreviousData,
  });
}
