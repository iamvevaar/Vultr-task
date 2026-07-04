"use client";

/**
 * App-wide client providers. Right now just React Query, which gives us data
 * fetching with caching, loading/error states, polling, and optimistic updates
 * — all the behaviours the task requires. We'll add a toast provider later when
 * we build optimistic UI.
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { AuthModalProvider } from "@/components/auth/auth-modal";

export function Providers({ children }: { children: React.ReactNode }) {
  // useState(() => ...) creates the client once per browser session (not on
  // every render), which is the recommended pattern in the App Router.
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 10_000, // treat data as fresh for 10s
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthModalProvider>{children}</AuthModalProvider>
    </QueryClientProvider>
  );
}
