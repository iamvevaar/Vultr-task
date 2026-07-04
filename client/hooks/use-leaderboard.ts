/** useLeaderboard — users ranked by total points, paginated. */

import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { LeaderboardPage } from "@/lib/types";
import { POLL_INTERVAL_MS } from "@/hooks/use-challenges";

export function useLeaderboard(page: number, limit = 20) {
  return useQuery({
    queryKey: ["leaderboard", page, limit],
    queryFn: () => apiFetch<LeaderboardPage>(`/leaderboard?page=${page}&limit=${limit}`),
    placeholderData: keepPreviousData,
    refetchInterval: POLL_INTERVAL_MS, // points change as rewards disburse
  });
}
