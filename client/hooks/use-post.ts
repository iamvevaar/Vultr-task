/** usePost — fetch a single thread (post + nested comments). Public/optional-auth. */

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { PostDetail } from "@/lib/types";

export const postQueryKey = (id: number) => ["post", id] as const;

export function usePost(id: number) {
  return useQuery({
    queryKey: postQueryKey(id),
    queryFn: () => apiFetch<PostDetail>(`/posts/${id}`),
    enabled: Number.isFinite(id) && id > 0,
  });
}
