"use client";

/**
 * A real React error boundary. React Query's isError handles *fetch* failures;
 * this catches unexpected *render* errors so a crash in one section shows a
 * visible fallback (with a reset) instead of blanking the whole page.
 */

import { Component, type ReactNode } from "react";

import { Button } from "@/components/ui/button";

type Props = { children: ReactNode; label?: string };
type State = { hasError: boolean };

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: unknown) {
    // In a real app this would go to an error reporter (Sentry, etc.).
    console.error("ErrorBoundary caught:", error);
  }

  reset = () => this.setState({ hasError: false });

  render() {
    if (this.state.hasError) {
      return (
        <div className="rounded-xl border border-border bg-surface-2 p-6 text-center">
          <p className="text-sm text-muted-foreground">
            Something went wrong{this.props.label ? ` loading ${this.props.label}` : ""}.
          </p>
          <Button variant="outline" size="sm" className="mt-3" onClick={this.reset}>
            Try again
          </Button>
        </div>
      );
    }
    return this.props.children;
  }
}
