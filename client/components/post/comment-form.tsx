"use client";

import { useState } from "react";

import { useAddComment } from "@/hooks/use-comments";
import { Button } from "@/components/ui/button";

export function CommentForm({
  postId,
  parentId = null,
  onDone,
  placeholder = "Write a comment…",
  autoFocus = false,
}: {
  postId: string;
  parentId?: string | null;
  onDone?: () => void;
  placeholder?: string;
  autoFocus?: boolean;
}) {
  const [body, setBody] = useState("");
  const add = useAddComment(postId);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const text = body.trim();
    if (!text) return;
    // Optimistic: the comment appears immediately, so we clear + close right away.
    add.mutate({ body: text, parentId });
    setBody("");
    onDone?.();
  };

  return (
    <form onSubmit={submit} className="space-y-2">
      <textarea
        autoFocus={autoFocus}
        rows={3}
        value={body}
        onChange={(e) => setBody(e.target.value)}
        placeholder={placeholder}
        className="w-full resize-y rounded-lg border border-input bg-surface-3/40 px-3 py-2 text-sm outline-none placeholder:text-subtle focus-visible:ring-2 focus-visible:ring-ring/50"
      />
      <div className="flex justify-end gap-2">
        {onDone && (
          <Button type="button" variant="ghost" size="sm" onClick={onDone}>
            Cancel
          </Button>
        )}
        <Button type="submit" size="sm" disabled={!body.trim()}>
          {parentId ? "Reply" : "Comment"}
        </Button>
      </div>
    </form>
  );
}
