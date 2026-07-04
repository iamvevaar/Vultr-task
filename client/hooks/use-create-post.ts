/**
 * useCreatePost — optimistic post creation (a task requirement).
 *
 * On submit we prepend a temporary post to the default feed cache so it shows
 * up instantly when the user lands on the feed. On error we roll the feed back
 * and toast; onSettled we refetch so the temp post is replaced by the real one.
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { apiFetch } from "@/lib/api";
import type { Paginated, PostDetail, PostSummary } from "@/lib/types";
import { useCurrentUser } from "@/hooks/use-current-user";

// Must match usePosts' default key: ["posts", sort, page, limit].
const LATEST_FEED_KEY = ["posts", "latest", 1, 10] as const;

export function useCreatePost() {
  const queryClient = useQueryClient();
  const { data: user } = useCurrentUser();

  return useMutation({
    mutationFn: (vars: { title: string; body: string }) =>
      apiFetch<PostDetail>("/posts", { method: "POST", body: JSON.stringify(vars) }),

    onMutate: async (vars) => {
      await queryClient.cancelQueries({ queryKey: ["posts"] });
      const previous = queryClient.getQueryData<Paginated<PostSummary>>(LATEST_FEED_KEY);

      if (previous && user) {
        const optimistic: PostSummary = {
          id: -Date.now(),
          title: vars.title,
          body: vars.body,
          author: { id: user.id, username: user.username },
          view_count: 0,
          comment_count: 0,
          created_at: new Date().toISOString(),
        };
        queryClient.setQueryData<Paginated<PostSummary>>(LATEST_FEED_KEY, {
          ...previous,
          data: [optimistic, ...previous.data],
          meta: { ...previous.meta, total: previous.meta.total + 1 },
        });
      }
      return { previous };
    },

    onError: (_err, _vars, context) => {
      if (context?.previous) queryClient.setQueryData(LATEST_FEED_KEY, context.previous);
      toast.error("Couldn't publish your post. Please try again.");
    },

    onSuccess: () => toast.success("Post published."),

    onSettled: () => queryClient.invalidateQueries({ queryKey: ["posts"] }),
  });
}
