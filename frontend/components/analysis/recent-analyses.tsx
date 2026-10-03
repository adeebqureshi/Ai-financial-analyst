"use client";

import { useMemo } from "react";
import Link from "next/link";
import { Search } from "lucide-react";

import { CompanyLogo } from "@/components/company/company-logo";
import { useChatSessions, chatSessionRows } from "@/hooks/use-chat-sessions";
import { EmptyState } from "@/components/ui/empty-state";
import { SkeletonList } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

const MAX_ITEMS = 4;
const TICKER_PATTERN = /^[A-Z]{1,5}$/;

function toTimestamp(value: string | null | undefined): number {
  if (!value) return 0;

  const parsed = new Date(value).getTime();
  return Number.isNaN(parsed) ? 0 : parsed;
}

function absoluteTime(value: string | null | undefined): string {
  if (!value) return "Recently";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Recently";

  return parsed.toLocaleString(undefined, {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Recent analyses — the workspace's real persisted research sessions.
 *
 * The backend persists AI chat sessions and documents only; analyses
 * themselves are recomputed on demand and never stored. So this list shows the
 * sessions that exist, links each one to its live analysis when the session
 * title is a ticker symbol, and renders an honest empty state otherwise. No
 * fabricated companies or dates.
 */
export function RecentAnalyses() {
  const sessions = useChatSessions();

  const rows = useMemo(
    () =>
      chatSessionRows(sessions.data)
        .map((session) => ({
          sessionId: session.session_id,
          title: session.title?.trim() || "Research session",
          timestamp: toTimestamp(session.updated_at),
          updatedAt: session.updated_at,
        }))
        .sort((a, b) => b.timestamp - a.timestamp)
        .slice(0, MAX_ITEMS),
    [sessions.data]
  );

  return (
    <section aria-labelledby="recent-analyses-heading" className="space-y-3">
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2">
        <div className="min-w-0">
          <h2 id="recent-analyses-heading" className="text-title text-foreground">
            Recent analyses
          </h2>
          <p className="mt-1 text-label text-muted-foreground">
            Your latest company analyses, continue where you left off.
          </p>
        </div>

        </div>

      {sessions.isPending ? (
        <div role="status" aria-busy="true">
          <SkeletonList items={2} />
          <span className="sr-only">Loading recent analyses…</span>
        </div>
      ) : rows.length === 0 ? (
        <EmptyState
          compact
          tone="brand"
          icon={<Search size={18} aria-hidden="true" />}
          title="No recent analyses yet"
          description="Run your first analysis above — your sessions show up here so you can pick up where you left off."
        />
      ) : (
        <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          {rows.map((row) => {
            const symbol = TICKER_PATTERN.test(row.title.trim())
              ? row.title.trim()
              : null;
            const href = symbol ? `/analysis/${symbol}` : "/analysis";

            return (
              <li key={row.sessionId}>
                <Link
                  href={href}
                  className={cn(
                    "group flex items-center gap-3 rounded-xl border border-border bg-card p-3.5 shadow-card",
                    "transition-[border-color,box-shadow] duration-150",
                    "hover:border-border-strong hover:shadow-soft",
                    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                    "focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                  )}
                >
                  {symbol ? (
                    // A recognised ticker gets its real brand mark; an
                    // unrecognised session title keeps the neutral "AI" badge,
                    // so no company identity is invented.
                    <CompanyLogo ticker={symbol} size="md" decorative />
                  ) : (
                    <span
                      className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand-subtle text-label font-semibold text-brand"
                      aria-hidden="true"
                    >
                      AI
                    </span>
                  )}

                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-label font-semibold text-foreground">
                      {row.title}
                    </span>
                    <span className="tnum mt-0.5 block truncate text-caption text-muted-foreground">
                      {absoluteTime(row.updatedAt)}
                    </span>
                  </span>

                  <span className="sr-only">Open analysis</span>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}