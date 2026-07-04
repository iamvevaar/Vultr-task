/**
 * Comment mutations for a post.
 *
 * useAddComment implements OPTIMISTIC UI (a task requirement): the new comment
 * shows up instantly in the cached thread, before the server confirms. On error
 * we roll the cache back to the snapshot and toast. onSettled we refetch to
 * reconcile the temporary comment with the real one (real id, server timestamp).
 *
 * useMarkSolution isn't optimistic — the server returns the updated PostDetail,
 * which we drop straight into the cache.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { apiFetch } from "@/lib/api";
import type { CommentNode, PostDetail } from "@/lib/types";
import { postQueryKey } from "@/hooks/use-post";
import { useCurrentUser } from "@/hooks/use-current-user";

/** Immutably insert a comment into the tree — as a root, or under a parent. */
function insertComment(post: PostDetail, comment: CommentNode, parentId: number | null): PostDetail {
  if (parentId === null) {
    return { ...post, comment_count: post.comment_count + 1, comments: [...post.comments, comment] };
  }
  const addToChildren = (nodes: CommentNode[]): CommentNode[] =>
    nodes.map((n) =>
      n.id === parentId
        ? { ...n, replies: [...n.replies, comment] }
        : { ...n, replies: addToChildren(n.replies) }
    );
  return { ...post, comment_count: post.comment_count + 1, comments: addToChildren(post.comments) };
}

type AddVars = { body: string; parentId?: number | null };

export function useAddComment(postId: number) {
  const queryClient = useQueryClient();
  const { data: user } = useCurrentUser();
  const key = postQueryKey(postId);

  return useMutation({
    mutationFn: ({ body, parentId }: AddVars) =>
      apiFetch<CommentNode>(`/posts/${postId}/comments`, {
        method: "POST",
        body: JSON.stringify({ body, parent_comment_id: parentId ?? null }),
      }),

    onMutate: async ({ body, parentId }: AddVars) => {
      await queryClient.cancelQueries({ queryKey: key });
      const previous = queryClient.getQueryData<PostDetail>(key);

      if (previous && user) {
        const optimistic: CommentNode = {
          id: -Date.now(), // temporary negative id, replaced on refetch
          body,
          author: { id: user.id, username: user.username },
          parent_comment_id: parentId ?? null,
          is_solution: false,
          created_at: new Date().toISOString(),
          replies: [],
        };
        queryClient.setQueryData<PostDetail>(key, insertComment(previous, optimistic, parentId ?? null));
      }
      return { previous };
    },

    onError: (_err, _vars, context) => {
      if (context?.previous) queryClient.setQueryData(key, context.previous);
      toast.error("Couldn't post your comment. Please try again.");
    },

    onSettled: () => queryClient.invalidateQueries({ queryKey: key }),
  });
}

export function useMarkSolution(postId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (commentId: number) =>
      apiFetch<PostDetail>(`/posts/${postId}/solution/${commentId}`, { method: "PATCH" }),
    onSuccess: (updated) => queryClient.setQueryData(postQueryKey(postId), updated),
    onError: () => toast.error("Couldn't mark the solution."),
  });
}
