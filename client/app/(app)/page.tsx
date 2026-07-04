/**
 * Home = the Feed, shown inside Shell A. Public: guests can read.
 * (Placeholder content for now — the real post list is the next step.)
 */
export default function HomePage() {
  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="text-2xl font-semibold">Developer Community</h1>
      <p className="mt-1 text-sm text-muted-foreground">
        Ask questions, share what you&apos;ve learned, and earn rewards.
      </p>

      <div className="mt-5 flex gap-5 border-b border-border">
        <span className="border-b-2 border-primary pb-2 text-sm font-medium">Latest</span>
        <span className="cursor-pointer pb-2 text-sm text-muted-foreground hover:text-foreground">
          Trending
        </span>
      </div>

      <div className="mt-6 rounded-xl border border-dashed border-border bg-surface-2/40 p-10 text-center text-sm text-muted-foreground">
        The feed lands here next.
      </div>
    </div>
  );
}
