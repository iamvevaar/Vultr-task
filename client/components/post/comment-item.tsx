"use client";

import { useState } from "react";
import { CheckCircle2 } from "lucide-react";

import { cn } from "@/lib/utils";
import { timeAgo } from "@/lib/format";
import type { CommentNode } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { CommentForm } from "./comment-form";

export function CommentItem({
  comment,
  postId,
  isOwner,
  canReply,
  onMarkSolution,
  marking,
}: {
  comment: CommentNode;
  postId: string;
  isOwner: boolean;
  canReply: boolean;
  onMarkSolution: (commentId: string) => void;
  marking: boolean;
}) {
  const [replying, setReplying] = useState(false);
  const isOptimistic = comment.id.startsWith("temp-"); // temp id → hide actions until reconciled

  return (
    <div>
      <div
        className={cn(
          "rounded-lg border p-3",
          comment.is_solution ? "border-success/40 bg-success/5" : "border-border bg-surface-2"
        )}
      >
        <div className="flex items-center gap-2 text-xs">
          <div className="grid size-6 shrink-0 place-items-center rounded-full bg-surface-3 text-[10px] font-medium">
            {comment.author.username.slice(0, 2).toUpperCase()}
          </div>
          <span className="font-mono text-muted-foreground">@{comment.author.username}</span>
          <span className="text-subtle">· {timeAgo(comment.created_at)}</span>
          {comment.is_solution && (
            <span className="ml-auto flex items-center gap-1 font-medium text-success">
              <CheckCircle2 className="size-3.5" /> Solution
            </span>
          )}
        </div>

        <p className="mt-2 whitespace-pre-wrap text-sm">{comment.body}</p>

        {!isOptimistic && (
          <div className="mt-2 flex items-center gap-1">
            {canReply && (
              <Button variant="ghost" size="xs" onClick={() => setReplying((v) => !v)}>
                Reply
              </Button>
            )}
            {isOwner && !comment.is_solution && (
              <Button variant="ghost" size="xs" onClick={() => onMarkSolution(comment.id)} disabled={marking}>
                Mark as solution
              </Button>
            )}
          </div>
        )}

        {replying && (
          <div className="mt-2">
            <CommentForm
              postId={postId}
              parentId={comment.id}
              autoFocus
              placeholder="Write a reply…"
              onDone={() => setReplying(false)}
            />
          </div>
        )}
      </div>

      {/* Nested replies, indented with a rail */}
      {comment.replies.length > 0 && (
        <div className="mt-2 ml-3 space-y-2 border-l border-border pl-3 sm:pl-4">
          {comment.replies.map((reply) => (
            <CommentItem
              key={reply.id}
              comment={reply}
              postId={postId}
              isOwner={isOwner}
              canReply={canReply}
              onMarkSolution={onMarkSolution}
              marking={marking}
            />
          ))}
        </div>
      )}
    </div>
  );
}
