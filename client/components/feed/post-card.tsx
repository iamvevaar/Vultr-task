import Link from "next/link";
import { MessageSquare } from "lucide-react";

import type { PostSummary } from "@/lib/types";
import { timeAgo } from "@/lib/format";

export function PostCard({ post }: { post: PostSummary }) {
  return (
    <Link
      href={`/posts/${post.id}`}
      className="block rounded-xl bg-surface-2 p-4 transition-colors hover:bg-surface-3/60"
    >
      <div className="flex items-start gap-3">
        <div className="grid size-9 shrink-0 place-items-center rounded-full bg-surface-3 text-xs font-medium">
          {post.author.username.slice(0, 2).toUpperCase()}
        </div>
        <div className="min-w-0 flex-1">
          <h3 className="font-medium leading-snug">{post.title}</h3>
          <p className="mt-1 line-clamp-2 text-sm text-muted-foreground">{post.body}</p>
          <div className="mt-2 flex items-center gap-3 text-xs text-subtle">
            <span className="font-mono">@{post.author.username}</span>
            <span aria-hidden>·</span>
            <span>{timeAgo(post.created_at)}</span>
            <span className="ml-auto flex items-center gap-1">
              <MessageSquare className="size-3.5" /> {post.comment_count}
            </span>
          </div>
        </div>
      </div>
    </Link>
  );
}
