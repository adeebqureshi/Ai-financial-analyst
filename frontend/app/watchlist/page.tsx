import { AppShell } from "@/components/layout/app-shell";

export default function WatchlistPage() {
  return (
    <AppShell>
      <div className="mx-auto max-w-7xl">
        <h1 className="text-3xl font-bold tracking-tight text-white">
          Watchlist
        </h1>

        <p className="mt-3 text-zinc-400">
          Monitor companies you are tracking.
        </p>
      </div>
    </AppShell>
  );
}