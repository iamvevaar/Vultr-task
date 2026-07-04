import { PostDetail } from "@/components/post/post-detail";

/** Thread page. params is async in the App Router, so we await it. */
export default async function PostPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <PostDetail postId={Number(id)} />;
}
