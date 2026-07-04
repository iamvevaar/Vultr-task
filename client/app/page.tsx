"use client";

/**
 * Temporary home page — a plumbing smoke test.
 *
 * It calls the backend's /health endpoint through our apiFetch + React Query.
 * If it shows "ok / connected", the whole chain works: env var -> API client ->
 * CORS -> FastAPI -> back to the UI. We'll replace this with the real Feed next.
 */

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";

type Health = { status: string; database: string };

export default function Home() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["health"],
    queryFn: () => apiFetch<Health>("/health"),
  });

  return (
    <main className="mx-auto max-w-md p-8">
      <h1 className="text-xl font-semibold">Plumbing check</h1>
      <p className="mt-1 text-sm text-gray-500">
        Frontend → API base: <code>{process.env.NEXT_PUBLIC_API_BASE_URL}</code>
      </p>

      <div className="mt-6 rounded-lg border p-4">
        {isLoading && <p>Checking backend…</p>}
        {error && <p className="text-red-600">Failed to reach backend: {(error as Error).message}</p>}
        {data && (
          <p className="text-green-600">
            ✓ Backend reachable — status: <b>{data.status}</b>, database: <b>{data.database}</b>
          </p>
        )}
      </div>
    </main>
  );
}
