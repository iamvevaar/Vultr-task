/**
 * Challenge/progress/streak queries — all POLLED.
 *
 * Why poll: challenge evaluation is async (a background worker), so progress and
 * rewards land a moment AFTER an action, without a page reload. We refetch every
 * 30s: comfortably above the worker's ~2s latency (so updates feel live), yet
 * gentle on the server compared with hammering it every few seconds.
 */

import { useQuery } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { ChallengeWithProgress, StreaksResponse } from "@/lib/types";

export const POLL_INTERVAL_MS = 30_000;

export function useChallenges() {
  return useQuery({
    queryKey: ["challenges"],
    queryFn: () => apiFetch<ChallengeWithProgress[]>("/challenges"),
    refetchInterval: POLL_INTERVAL_MS,
  });
}

export function useStreaks() {
  return useQuery({
    queryKey: ["streaks"],
    queryFn: () => apiFetch<StreaksResponse>("/users/me/streaks"),
    refetchInterval: POLL_INTERVAL_MS,
  });
}

export function useWeeklyChallenge() {
  return useQuery({
    queryKey: ["challenge-weekly"],
    queryFn: () => apiFetch<ChallengeWithProgress | null>("/challenges/weekly"),
    refetchInterval: POLL_INTERVAL_MS,
  });
}
