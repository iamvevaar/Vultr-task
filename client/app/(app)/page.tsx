import { Suspense } from "react";

import { Feed } from "@/components/feed/feed";
import { FeedSkeleton } from "@/components/feed/feed-skeleton";

/** Home = the Feed, inside Shell A. Public: guests can read. */
export default function HomePage() {
  // Suspense boundary is required because <Feed> reads the URL via useSearchParams.
  return (
    <Suspense fallback={<div className="mx-auto max-w-2xl pt-20"><FeedSkeleton /></div>}>
      <Feed />
    </Suspense>
  );
}
