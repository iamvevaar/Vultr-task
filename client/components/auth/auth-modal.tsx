"use client";

/**
 * The auth modal + a context to open it from anywhere.
 *
 * Instead of navigating to a /login page, any action that needs auth calls
 * useAuthModal().open() and this animated dialog appears. It handles both login
 * and register in one place (toggle with the footer link). On success it primes
 * the ["me"] cache so the whole app instantly knows you're signed in.
 */

import { createContext, useContext, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { apiFetch } from "@/lib/api";
import type { AuthResponse } from "@/lib/types";
import { ME_QUERY_KEY } from "@/hooks/use-current-user";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type Mode = "login" | "register";

type AuthModalContextValue = { open: (mode?: Mode) => void; close: () => void };

const AuthModalContext = createContext<AuthModalContextValue | null>(null);

export function useAuthModal() {
  const ctx = useContext(AuthModalContext);
  if (!ctx) throw new Error("useAuthModal must be used within <AuthModalProvider>");
  return ctx;
}

export function AuthModalProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [mode, setMode] = useState<Mode>("login");

  const open = (m: Mode = "login") => {
    setMode(m);
    setIsOpen(true);
  };

  return (
    <AuthModalContext.Provider value={{ open, close: () => setIsOpen(false) }}>
      {children}
      <AuthModal isOpen={isOpen} setIsOpen={setIsOpen} mode={mode} setMode={setMode} />
    </AuthModalContext.Provider>
  );
}

function AuthModal({
  isOpen,
  setIsOpen,
  mode,
  setMode,
}: {
  isOpen: boolean;
  setIsOpen: (v: boolean) => void;
  mode: Mode;
  setMode: (m: Mode) => void;
}) {
  const queryClient = useQueryClient();
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const submit = useMutation({
    mutationFn: () => {
      const path = mode === "login" ? "/auth/login" : "/auth/register";
      const body =
        mode === "login" ? { email, password } : { username, email, password };
      return apiFetch<AuthResponse>(path, { method: "POST", body: JSON.stringify(body) });
    },
    onSuccess: (data) => {
      queryClient.setQueryData(ME_QUERY_KEY, data.user);
      setIsOpen(false);
      setUsername("");
      setEmail("");
      setPassword("");
    },
  });

  const isLogin = mode === "login";

  return (
    <Dialog open={isOpen} onOpenChange={setIsOpen}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isLogin ? "Sign in" : "Create your account"}</DialogTitle>
          <DialogDescription>
            {isLogin
              ? "Welcome back to the Vultr Developer Community."
              : "Join the community to post, comment, and earn rewards."}
          </DialogDescription>
        </DialogHeader>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit.mutate();
          }}
          className="space-y-4"
        >
          {!isLogin && (
            <div className="space-y-2">
              <Label htmlFor="m-username">Username</Label>
              <Input
                id="m-username"
                required
                minLength={3}
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="yourname"
              />
            </div>
          )}
          <div className="space-y-2">
            <Label htmlFor="m-email">Email</Label>
            <Input
              id="m-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="m-password">Password</Label>
            <Input
              id="m-password"
              type="password"
              required
              minLength={isLogin ? undefined : 8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          {submit.isError && (
            <p className="text-sm text-destructive">{(submit.error as Error).message}</p>
          )}

          <Button type="submit" className="w-full" disabled={submit.isPending}>
            {submit.isPending ? "Please wait…" : isLogin ? "Sign in" : "Create account"}
          </Button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          {isLogin ? "New here? " : "Already have an account? "}
          <button
            type="button"
            className="text-primary underline-offset-4 hover:underline"
            onClick={() => {
              submit.reset();
              setMode(isLogin ? "register" : "login");
            }}
          >
            {isLogin ? "Create an account" : "Sign in"}
          </button>
        </p>
      </DialogContent>
    </Dialog>
  );
}
