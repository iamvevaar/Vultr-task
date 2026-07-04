/**
 * useCurrentUser — a small custom hook with one job: report who's logged in.
 *
 * It queries /auth/me. If the auth cookie is valid you get the User; if not,
 * the request 401s and `data` stays undefined (retry:false so we don't hammer
 * it). The ["me"] cache key is shared, so login/logout can update it directly.
 */

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { User } from "@/lib/types";

export const ME_QUERY_KEY = ["me"] as const;

export function useCurrentUser() {
  return useQuery({
    queryKey: ME_QUERY_KEY,
    queryFn: () => apiFetch<User>("/auth/me"),
    retry: false,          // a 401 means "not logged in", not "try again"
    staleTime: 60_000,
  });
}
