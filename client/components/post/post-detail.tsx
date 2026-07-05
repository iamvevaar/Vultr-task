"use client";

import Link from "next/link";
import { ArrowLeft, CheckCircle2 } from "lucide-react";

import { timeAgo } from "@/lib/format";
import type { CommentNode } from "@/lib/types";
import { usePost } from "@/hooks/use-post";
import { useCurrentUser } from "@/hooks/use-current-user";
import { useMarkSolution } from "@/hooks/use-comments";
import { useAuthModal } from "@/components/auth/auth-modal";
import { Button } from "@/components/ui/button";
import { CommentForm } from "./comment-form";
import { CommentItem } from "./comment-item";

/** Depth-first search for the accepted-solution comment. */
function findSolution(nodes: CommentNode[]): CommentNode | null {
  for (const n of nodes) {
    if (n.is_solution) return n;
    const found = findSolution(n.replies);
    if (found) return found;
  }
  return null;
}

export function PostDetail({ postId }: { postId: string }) {
  const { data: post, isLoading, isError, refetch } = usePost(postId);
  const { data: user } = useCurrentUser();
  const markSolution = useMarkSolution(postId);
  const authModal = useAuthModal();

  if (isLoading) return <PostSkeleton />;
  if (isError || !post) return <ErrorState onRetry={() => refetch()} />;

  const isOwner = !!user && user.id === post.author.id;
  const solution = post.solution_comment_id ? findSolution(post.comments) : null;

  return (
    <article className="mx-auto max-w-2xl">
      <Link href="/" className="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft className="size-4" /> Feed
      </Link>

      <h1 className="mt-3 text-2xl font-semibold">{post.title}</h1>
      <div className="mt-1 flex items-center gap-2 text-xs text-subtle">
        <span className="font-mono">@{post.author.username}</span>
        <span>· {timeAgo(post.created_at)}</span>
      </div>

      <p className="mt-4 whitespace-pre-wrap text-sm leading-relaxed text-foreground/90">{post.body}</p>

      {/* Accepted-solution highlight */}
      {solution && (
        <div className="mt-6 rounded-lg border border-success/40 bg-success/5 p-3">
          <p className="flex items-center gap-1 text-xs font-medium text-success">
            <CheckCircle2 className="size-4" /> Accepted solution
          </p>
          <p className="mt-2 whitespace-pre-wrap text-sm">{solution.body}</p>
          <p className="mt-2 font-mono text-xs text-subtle">— @{solution.author.username}</p>
        </div>
      )}

      <h2 className="mt-8 text-sm font-medium text-muted-foreground">
        {post.comment_count} {post.comment_count === 1 ? "comment" : "comments"}
      </h2>

      {/* Comment box (or sign-in prompt for guests) */}
      <div className="mt-4">
        {user ? (
          <CommentForm postId={postId} />
        ) : (
          <div className="flex items-center justify-between rounded-lg bg-surface-2 p-3">
            <span className="text-sm text-muted-foreground">Sign in to join the conversation.</span>
            <Button size="sm" onClick={() => authModal.open("login")}>
              Sign in
            </Button>
          </div>
        )}
      </div>

      {/* Thread */}
      <div className="mt-6 space-y-3">
        {post.comments.length === 0 ? (
          <p className="text-sm text-subtle">No comments yet.</p>
        ) : (
          post.comments.map((comment) => (
            <CommentItem
              key={comment.id}
              comment={comment}
              postId={postId}
              isOwner={isOwner}
              canReply={!!user}
              onMarkSolution={(id) => markSolution.mutate(id)}
              marking={markSolution.isPending}
            />
          ))
        )}
      </div>
    </article>
  );
}

function PostSkeleton() {
  return (
    <div className="mx-auto max-w-2xl space-y-4">
      <div className="h-4 w-16 animate-pulse rounded bg-surface-3" />
      <div className="h-7 w-2/3 animate-pulse rounded bg-surface-3" />
      <div className="h-3 w-40 animate-pulse rounded bg-surface-3" />
      <div className="space-y-2 pt-2">
        <div className="h-3 w-full animate-pulse rounded bg-surface-3" />
        <div className="h-3 w-5/6 animate-pulse rounded bg-surface-3" />
      </div>
    </div>
  );
}

function ErrorState({ onRetry }: { onRetry: () => void }) {
  return (
    <div className="mx-auto max-w-2xl rounded-xl bg-surface-2 p-8 text-center">
      <p className="text-sm text-muted-foreground">Couldn&apos;t load this thread.</p>
      <Button variant="outline" size="sm" className="mt-3" onClick={onRetry}>
        Retry
      </Button>
    </div>
  );
}
