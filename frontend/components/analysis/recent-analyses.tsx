"use client";

import { useMemo } from "react";
import Link from "next/link";
import { ArrowUpRight, MessageSquare } from "lucide-react";

import { CompanyLogo } from "@/components/company/company-logo";
import { useChatSessions, chatSessionRows } from "@/hooks/use-chat-sessions";
import { SkeletonList } from "@/components/ui/skeleton";

const MAX_ITEMS = 6;
const TICKER_PATTERN = /^[A-Z]{1,5}$/;

function toTimestamp(value: string | null | undefined): number {
  if (!value) return 0;

  const parsed = new Date(value).getTime();
  return Number.isNaN(parsed) ? 0 : parsed;
}

/**
 * Relative time from the session's real `updated_at`.
 *
 * Anything older than a week falls back to an absolute date, because
 * "43 days ago" is not useful to a reader.
 */
function relativeTime(value: string | null | undefined): string {
  if (!value) return "—";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "—";

  const seconds = Math.round((Date.now() - parsed.getTime()) / 1000);

  if (seconds < 60) return "Just now";

  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes} min ago`;

  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hr ago`;

  const days = Math.round(hours / 24);
  if (days === 1) return "Yesterday";
  if (days < 7) return `${days} days ago`;

  return parsed.toLocaleDateString(undefined, {
    day: "2-digit",
    month: "short",
    year: parsed.getFullYear() === new Date().getFullYear() ? undefined : "numeric",
  });
}

/**
 * Recent research sessions — the workspace's real persisted history.
 *
 * The backend persists AI chat sessions and documents only; analyses
 * themselves are recomputed on demand and never stored. So this lists the
 * sessions that exist, links each to its live analysis when the title is a
 * ticker symbol, and renders an honest empty state otherwise. No fabricated
 * companies or dates.
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
    <section aria-labelledby="recent-sessions-heading" className="space-y-2">
      <h2 id="recent-sessions-heading" className="text-title text-foreground">
        Recent research sessions
      </h2>

      {sessions.isPending ? (
        <div role="status" aria-busy="true">
          <SkeletonList items={3} />
          <span className="sr-only">Loading recent research sessions…</span>
        </div>
      ) : rows.length === 0 ? (
        <p className="text-label text-muted-foreground">
          No research sessions yet. Analyze a company above and your
          conversations are saved here.
        </p>
      ) : (
        <ul className="divide-y divide-border border-y border-border">
          {rows.map((row) => {
            const symbol = TICKER_PATTERN.test(row.title.trim())
              ? row.title.trim()
              : null;
            const href = symbol ? `/analysis/${symbol}` : "/analysis";

            return (
              <li key={row.sessionId}>
                <Link
                  href={href}
                  className="group flex items-center gap-3 py-2.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
                >
                  {symbol ? (
                    // A recognised ticker gets its real brand mark; an
                    // unrecognised session title keeps the neutral "AI" badge,
                    // so no company identity is invented.
                    <CompanyLogo ticker={symbol} size="xs" decorative />
                  ) : (
                    <MessageSquare
                      size={16}
                      className="shrink-0 text-subtle-foreground"
                      aria-hidden="true"
                    />
                  )}

                  <span className="min-w-0 flex-1 truncate text-label font-medium text-foreground">
                    {row.title}
                  </span>

                  <span className="tnum shrink-0 text-caption text-muted-foreground">
                    {relativeTime(row.updatedAt)}
                  </span>

                  <ArrowUpRight
                    size={15}
                    className="shrink-0 text-subtle-foreground transition-colors group-hover:text-brand"
                    aria-hidden="true"
                  />

                  <span className="sr-only">Open research session</span>
                </Link>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}