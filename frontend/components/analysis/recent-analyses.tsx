"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { ArrowUpRight, MessageSquare } from "lucide-react";

import { CompanyLogo } from "@/components/company/company-logo";
import {
  useChatSessions,
  chatSessionRows,
  useDeleteChatSession,
} from "@/hooks/use-chat-sessions";
import { ConfirmDialog } from "@/components/ui/confirm-dialog";
import { Button } from "@/components/ui/button";
import { SkeletonList } from "@/components/ui/skeleton";

import { SessionActionsMenu } from "./session-actions-menu";

const MAX_ITEMS = 6;
const TICKER_PATTERN = /^[A-Z]{1,5}$/;
const FALLBACK_TITLE = "Research session";

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
 * The backend persists AI chat sessions and documents only; analyses themselves
 * are recomputed on demand and never stored. So this lists the sessions that
 * exist, links each to its live analysis when the title is a ticker symbol, and
 * renders an honest empty state otherwise. No fabricated companies or dates.
 *
 * Each row can be deleted, which removes the session and its messages from
 * persistent storage — it is not a client-side hide.
 */
export function RecentAnalyses() {
  const sessions = useChatSessions();
  const deleteSession = useDeleteChatSession();

  // Session id awaiting confirmation, plus the delete error surfaced below.
  const [pendingId, setPendingId] = useState<string | null>(null);

  const rows = useMemo(
    () =>
      chatSessionRows(sessions.data)
        .map((session) => ({
          sessionId: session.session_id,
          // The backend derives the title from the first question actually
          // asked. The fallback only applies to a session with no messages at
          // all — it never invents a company or a subject.
          title: session.title?.trim() || FALLBACK_TITLE,
          timestamp: toTimestamp(session.updated_at),
          updatedAt: session.updated_at,
        }))
        .sort((a, b) => b.timestamp - a.timestamp)
        .slice(0, MAX_ITEMS),
    [sessions.data]
  );

  const pendingRow = rows.find((row) => row.sessionId === pendingId) ?? null;
  const isDeleting = deleteSession.isPending;

  async function confirmDelete() {
    if (!pendingId || isDeleting) return;

    try {
      await deleteSession.mutateAsync(pendingId);
      setPendingId(null);
    } catch {
      // Left to the mutation's error state; the dialog stays open so the user
      // sees the failure and can retry or cancel. The row is NOT removed.
    }
  }

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
            const busy = isDeleting && pendingId === row.sessionId;

            return (
              <li key={row.sessionId} className="flex items-center gap-1">
                {/* The row is a link plus a sibling menu, never a button nested
                    inside an anchor. */}
                <Link
                  href={href}
                  className="group flex min-w-0 flex-1 items-center gap-3 py-2.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
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

                <SessionActionsMenu
                  sessionId={row.sessionId}
                  href={href}
                  sessionLabel={row.title}
                  onRequestDelete={() => setPendingId(row.sessionId)}
                  busy={busy}
                />
              </li>
            );
          })}
        </ul>
      )}

      {deleteSession.isError && (
        // Deliberately not `ErrorDisplay`: that component falls back to
        // `error.message`, which for a 4xx is whatever text the backend sent.
        // Deletion failure gets one fixed, friendly sentence instead, so no
        // server detail (and certainly no trace) can reach the user.
        <div
          role="alert"
          className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-loss/25 bg-loss-subtle px-3.5 py-2.5"
        >
          <p className="text-caption text-loss">
            Couldn&apos;t delete this research session. Please try again.
          </p>

          {pendingId && (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => void confirmDelete()}
            >
              Try again
            </Button>
          )}
        </div>
      )}

      <ConfirmDialog
        open={pendingRow !== null}
        title="Delete research session?"
        description={
          <>
            This will permanently delete this research session and its
            conversation history
            {pendingRow ? (
              <>
                {" "}
                (<span className="font-medium text-foreground">{pendingRow.title}</span>)
              </>
            ) : null}
            . This cannot be undone.
          </>
        }
        confirmLabel="Delete"
        cancelLabel="Cancel"
        pending={isDeleting}
        onConfirm={() => void confirmDelete()}
        onCancel={() => {
          if (isDeleting) return;
          setPendingId(null);
        }}
      />
    </section>
  );
}