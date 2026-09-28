"use client";

import { useRouter } from "next/navigation";
import { MessageSquare, Sparkles } from "lucide-react";

import { useChatSessions, chatSessionRows } from "@/hooks/use-chat-sessions";
import { useCopilot } from "@/components/layout/ai-copilot";
import { SectionHeading } from "@/components/ui/page-header";
import { Button } from "@/components/ui/button";
import { SkeletonList } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";

function relativeTime(value: string | null): string {
  if (!value) return "Recent session";

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Recent session";

  const deltaMs = Date.now() - parsed.getTime();
  const minutes = Math.round(deltaMs / 60_000);

  if (minutes < 1) return "Just now";
  if (minutes < 60) return `${minutes} min ago`;

  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} h ago`;

  const days = Math.round(hours / 24);
  if (days < 7) return `${days} d ago`;

  return parsed.toLocaleDateString();
}

export function RecentInsights() {
  const router = useRouter();
  const copilot = useCopilot();
  const sessions = useChatSessions();
  const rows = chatSessionRows(sessions.data).slice(0, 5);

  return (
    <section aria-labelledby="recent-insights-heading" className="space-y-4">
      <SectionHeading
        id="recent-insights-heading"
        title="Recent AI insights"
        description="Your latest copilot research sessions, restored from the workspace."
        actions={
          <Button
            variant="subtle"
            size="sm"
            onClick={() => copilot.open()}
            className="hidden sm:inline-flex"
          >
            <Sparkles size={14} aria-hidden="true" />
            New question
          </Button>
        }
      />

      {sessions.isPending ? (
        <div role="status" aria-busy="true">
          <SkeletonList items={3} />
          <span className="sr-only">Loading recent AI sessions…</span>
        </div>
      ) : sessions.isError ? (
        <div
          className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-border bg-card px-4 py-3.5"
          role="status"
        >
          <p className="text-label text-muted-foreground">
            Recent sessions are unavailable right now. New questions still work.
          </p>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => sessions.refetch()}
          >
            Try again
          </Button>
        </div>
      ) : rows.length === 0 ? (
        <EmptyState
          compact
          tone="brand"
          icon={<MessageSquare size={18} aria-hidden="true" />}
          title="No AI sessions yet"
          description="Ask a research question and it will be listed here for quick access."
          action={
            <Button variant="primary" size="sm" onClick={() => copilot.open()}>
              <Sparkles size={14} aria-hidden="true" />
              Ask your first question
            </Button>
          }
        />
      ) : (
        <ul className="divide-y divide-border overflow-hidden rounded-xl border border-border bg-card">
          {rows.map((session) => (
            <li key={session.session_id}>
              <button
                type="button"
                onClick={() => copilot.open({ sessionId: session.session_id })}
                className="group flex w-full items-center justify-between gap-4 px-4 py-3.5 text-left transition-colors hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
              >
                <span className="flex min-w-0 items-center gap-3">
                  <span
                    className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-brand-subtle text-brand"
                    aria-hidden="true"
                  >
                    <MessageSquare size={15} />
                  </span>

                  <span className="min-w-0">
                    <span className="block truncate text-label font-medium text-foreground">
                      {session.title ?? "Untitled research session"}
                    </span>
                    <span className="mt-0.5 block text-caption text-muted-foreground">
                      {relativeTime(session.updated_at)}
                    </span>
                  </span>
                </span>

                <span className="shrink-0 text-caption font-medium text-brand opacity-0 transition-opacity group-hover:opacity-100 group-focus-visible:opacity-100">
                  Continue
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}

      <div className="flex flex-wrap gap-2 sm:hidden">
        <Button variant="primary" size="sm" onClick={() => copilot.open()}>
          <Sparkles size={14} aria-hidden="true" />
          New question
        </Button>
        <Button
          variant="secondary"
          size="sm"
          onClick={() => router.push("/search")}
        >
          Search documents
        </Button>
      </div>
    </section>
  );
}
