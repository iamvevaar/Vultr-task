"use client";

/**
 * Shell A — the 3-column app frame used on every logged-in-or-not app page:
 *   [ sidebar (Layer 1) ] [ main content (Layer 0 canvas) ] [ right rail (Layer 1) ]
 *
 * Guests see the whole frame and can browse; auth-gated nav items and actions
 * open the login modal instead of navigating. Responsive: rails collapse on
 * small screens so the main column is full-width.
 */

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Home, LogOut, Medal, Plus, Trophy, User } from "lucide-react";

import { apiFetch } from "@/lib/api";
import { cn } from "@/lib/utils";
import { ME_QUERY_KEY, useCurrentUser } from "@/hooks/use-current-user";
import { useAuthModal } from "@/components/auth/auth-modal";
import { WeeklyWidget } from "@/components/challenges/weekly-widget";
import { LeaderboardPreview } from "@/components/leaderboard/leaderboard-preview";
import { ErrorBoundary } from "@/components/error-boundary";
import { Button, buttonVariants } from "@/components/ui/button";

const NAV = [
  { label: "Feed", href: "/", icon: Home, requiresAuth: false },
  { label: "Challenges", href: "/challenges", icon: Trophy, requiresAuth: true },
  { label: "Leaderboard", href: "/leaderboard", icon: Medal, requiresAuth: true },
  { label: "Profile", href: "/profile", icon: User, requiresAuth: true },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { data: user } = useCurrentUser();
  const authModal = useAuthModal();
  const queryClient = useQueryClient();

  const logout = useMutation({
    mutationFn: () => apiFetch("/auth/logout", { method: "POST" }),
    onSuccess: () => queryClient.setQueryData(ME_QUERY_KEY, null),
  });

  const navItemClass = (active: boolean) =>
    cn(
      "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
      active
        ? "bg-surface-3 text-foreground"
        : "text-muted-foreground hover:bg-surface-2 hover:text-foreground"
    );

  return (
    <div className="mx-auto flex h-screen w-full max-w-[1400px] overflow-hidden">
      {/* ---- Sidebar (Layer 1) — fixed full height, only main scrolls ---- */}
      <aside className="m-4 hidden h-[calc(100vh-2rem)] w-60 shrink-0 flex-col overflow-y-auto rounded-lg border border-border bg-surface-1 p-4 md:flex">
        <Link href="/" className="mb-6 flex items-center gap-2 px-1">
          <span className="fill-primary grid size-7 place-items-center rounded-md text-sm font-bold">V</span>
          <span className="text-base font-semibold">Vultr</span>
        </Link>

        <nav className="flex flex-col gap-1">
          {NAV.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href;
            if (item.requiresAuth && !user) {
              return (
                <button key={item.href} className={navItemClass(active)} onClick={() => authModal.open("login")}>
                  <Icon className="size-4" />
                  {item.label}
                </button>
              );
            }
            return (
              <Link key={item.href} href={item.href} className={navItemClass(active)}>
                <Icon className="size-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="mt-4">
          {user ? (
            <Link href="/posts/new" className={cn(buttonVariants(), "w-full")}>
              <Plus className="size-4" />
              New Post
            </Link>
          ) : (
            <Button className="w-full" onClick={() => authModal.open("login")}>
              <Plus className="size-4" />
              New Post
            </Button>
          )}
        </div>

        {/* user chip / sign-in, pinned to the bottom */}
        <div className="mt-auto pt-4">
          {user ? (
            <div className="flex items-center gap-2 rounded-lg bg-surface-2 p-2">
              <div className="grid size-8 shrink-0 place-items-center rounded-full bg-surface-3 text-xs font-medium">
                {user.username.slice(0, 2).toUpperCase()}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-medium">{user.username}</p>
                <p className="text-xs text-subtle">{user.role}</p>
              </div>
              <Button variant="ghost" size="icon-sm" title="Log out" onClick={() => logout.mutate()}>
                <LogOut className="size-4" />
              </Button>
            </div>
          ) : (
            <Button variant="outline" className="w-full" onClick={() => authModal.open("login")}>
              Sign in
            </Button>
          )}
        </div>
      </aside>

      {/* ---- Main (Layer 0 canvas) — the ONLY scrolling area ---- */}
      <main className="min-w-0 flex-1 overflow-y-auto px-4 py-6 sm:px-8">
        <ErrorBoundary label="this page">{children}</ErrorBoundary>
      </main>

      {/* ---- Right rail (Layer 1) — fixed full height ---- */}
      <aside className="m-4 hidden h-[calc(100vh-2rem)] w-72 shrink-0 flex-col gap-4 overflow-y-auto rounded-lg border border-border bg-surface-1 p-4 lg:flex">
        {/* Weekly widget is here in the shared layout → present on every page, polling live. */}
        <ErrorBoundary label="the weekly challenge">
          <WeeklyWidget />
        </ErrorBoundary>
        <ErrorBoundary label="the leaderboard">
          <LeaderboardPreview />
        </ErrorBoundary>
      </aside>
    </div>
  );
}
