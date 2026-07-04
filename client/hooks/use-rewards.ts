/**
 * useRewards — the paginated reward ledger + profile summary (points, badges).
 * Polls like the challenges page, since rewards are disbursed asynchronously
 * after the background worker evaluates a completion.
 */

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { RewardsPage } from "@/lib/types";
import { POLL_INTERVAL_MS } from "@/hooks/use-challenges";

export function useRewards(page: number, limit = 10) {
  return useQuery({
    queryKey: ["rewards", page, limit],
    queryFn: () => apiFetch<RewardsPage>(`/users/me/rewards?page=${page}&limit=${limit}`),
    placeholderData: keepPreviousData,
    refetchInterval: POLL_INTERVAL_MS,
  });
}
