/** usePost — fetch a single thread (post + nested comments). Public/optional-auth. */

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { PostDetail } from "@/lib/types";

export const postQueryKey = (id: string) => ["post", id] as const;

export function usePost(id: string) {
  return useQuery({
    queryKey: postQueryKey(id),
    queryFn: () => apiFetch<PostDetail>(`/posts/${id}`),
    enabled: !!id,
  });
}
