"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { ArrowLeft } from "lucide-react";

import { useCurrentUser } from "@/hooks/use-current-user";
import { useCreatePost } from "@/hooks/use-create-post";
import { useAuthModal } from "@/components/auth/auth-modal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function NewPostPage() {
  const router = useRouter();
  const { data: user, isLoading } = useCurrentUser();
  const authModal = useAuthModal();
  const create = useCreatePost();

  const [title, setTitle] = useState("");
  const [body, setBody] = useState("");

  if (isLoading) {
    return (
      <div className="mx-auto max-w-2xl space-y-4">
        <div className="h-7 w-40 animate-pulse rounded bg-surface-3" />
        <div className="h-10 w-full animate-pulse rounded bg-surface-3" />
        <div className="h-40 w-full animate-pulse rounded bg-surface-3" />
      </div>
    );
  }

  // Writes require auth — a guest who lands here directly gets a prompt.
  if (!user) {
    return (
      <div className="mx-auto max-w-2xl rounded-xl border border-border bg-surface-2 p-8 text-center">
        <p className="text-sm text-muted-foreground">You need to sign in to create a post.</p>
        <Button className="mt-3" onClick={() => authModal.open("login")}>
          Sign in
        </Button>
      </div>
    );
  }

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim() || !body.trim()) return;
    // Optimistic: fire the mutation, then land on the feed where the new post
    // already appears (rolls back + toasts there if the server rejects it).
    create.mutate({ title: title.trim(), body: body.trim() });
    router.push("/");
  };

  return (
    <div className="mx-auto max-w-2xl">
      <Link href="/" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" /> Feed
      </Link>

      <h1 className="mt-3 text-2xl font-semibold">Create a thread</h1>

      <form onSubmit={submit} className="mt-6 space-y-5">
        <div className="space-y-2">
          <Label htmlFor="title">Title</Label>
          <Input
            id="title"
            required
            maxLength={200}
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="A clear, specific question"
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="body">Body</Label>
          <textarea
            id="body"
            required
            rows={10}
            value={body}
            onChange={(e) => setBody(e.target.value)}
            placeholder="Describe what you've tried, expected vs. actual…"
            className="w-full resize-y rounded-lg border border-input bg-surface-3/40 px-3 py-2 text-sm outline-none placeholder:text-subtle focus-visible:ring-2 focus-visible:ring-ring/50"
          />
        </div>

        <div className="flex justify-end gap-2">
          <Link href="/" className="inline-flex items-center rounded-lg px-3 text-sm text-muted-foreground hover:text-foreground">
            Cancel
          </Link>
          <Button type="submit" disabled={!title.trim() || !body.trim()}>
            Publish
          </Button>
        </div>
      </form>
    </div>
  );
}
