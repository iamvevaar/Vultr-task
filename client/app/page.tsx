"use client";

/**
 * Temporary home page — plumbing + auth smoke test.
 * Confirms backend connectivity AND shows who's logged in (via the cookie).
 * We'll replace this with the real Feed soon.
 */

import Link from "next/link";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import { ME_QUERY_KEY, useCurrentUser } from "@/hooks/use-current-user";
import { Button } from "@/components/ui/button";

type Health = { status: string; database: string };

export default function Home() {
  const queryClient = useQueryClient();
  const health = useQuery({ queryKey: ["health"], queryFn: () => apiFetch<Health>("/health") });
  const { data: user, isLoading: userLoading } = useCurrentUser();

  const logout = useMutation({
    mutationFn: () => apiFetch("/auth/logout", { method: "POST" }),
    onSuccess: () => queryClient.setQueryData(ME_QUERY_KEY, null),
  });

  return (
    <main className="mx-auto max-w-md space-y-6 p-8">
      <h1 className="text-xl font-semibold">Plumbing check</h1>

      <section className="rounded-lg border p-4">
        <h2 className="mb-2 text-sm font-medium text-muted-foreground">Backend</h2>
        {health.isLoading && <p>Checking backend…</p>}
        {health.error && <p className="text-red-600">Failed: {(health.error as Error).message}</p>}
        {health.data && (
          <p className="text-green-600">
            ✓ status: <b>{health.data.status}</b>, database: <b>{health.data.database}</b>
          </p>
        )}
      </section>

      <section className="rounded-lg border p-4">
        <h2 className="mb-2 text-sm font-medium text-muted-foreground">Auth</h2>
        {userLoading ? (
          <p>Checking session…</p>
        ) : user ? (
          <div className="space-y-3">
            <p className="text-green-600">
              ✓ Logged in as <b>{user.username}</b> ({user.role})
            </p>
            <Button variant="outline" size="sm" onClick={() => logout.mutate()}>
              Log out
            </Button>
          </div>
        ) : (
          <div className="space-x-3">
            <span className="text-muted-foreground">Not logged in.</span>
            <Link href="/login" className="underline">Sign in</Link>
            <Link href="/register" className="underline">Register</Link>
          </div>
        )}
      </section>
    </main>
  );
}
