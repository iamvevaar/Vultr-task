import { AppShell } from "@/components/layout/app-shell";

/**
 * Layout for the main app pages — wraps them in Shell A (sidebar + main + rail).
 * The (auth) route group is intentionally OUTSIDE this, so login/register (the
 * page fallbacks) don't get the shell.
 */
export default function AppLayout({ children }: { children: React.ReactNode }) {
  return <AppShell>{children}</AppShell>;
}
