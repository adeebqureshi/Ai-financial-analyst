"use client";

import { Sparkles } from "lucide-react";

import { ChatSurface } from "@/components/ui/chat-surface";
import { cn } from "@/lib/utils";

import { useDocuments } from "@/hooks/use-documents";

/**
 * Example questions. Clicking one goes through `ChatSurface`'s existing `send()`
 * path, so suggestions hit the same RAG endpoint as a typed question — they are
 * not decorative.
 */
const RESEARCH_SUGGESTIONS = [
  "What are the key financial highlights in this document?",
  "Summarize the management commentary.",
  "What are the main risks and uncertainties?",
  "Give me a summary of the financial performance.",
];

type Props = {
  /** Document the assistant is grounded in; falls back to the whole library. */
  documentId: string | null;
  hasDocument: boolean;
};

/**
 * Right-hand "AI Research Assistant" panel.
 *
 * Reuses `ChatSurface` (streaming, citations, retry, new-chat, sessions) rather
 * than reimplementing a second chat system — only the surrounding framing and
 * height are adapted to the reference layout.
 */
export function ResearchAssistant({ documentId, hasDocument }: Props) {
  const { isPending } = useDocuments();

  return (
    <section
      aria-labelledby="research-assistant-heading"
      className="flex h-full flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-card"
    >
      <header className="shrink-0 px-5 pb-3 pt-5">
        <div className="flex items-center gap-3">
          <span
            className="flex size-10 shrink-0 items-center justify-center rounded-xl bg-brand-subtle text-brand ring-1 ring-brand/15"
            aria-hidden="true"
          >
            <Sparkles size={18} />
          </span>
          <div className="min-w-0">
            <h2
              id="research-assistant-heading"
              className="truncate text-[1.125rem] font-semibold tracking-[-0.01em] text-foreground"
            >
              AI Research Assistant
            </h2>
            {/* Real service state — never a hardcoded "Ready". */}
            <p className="mt-0.5 flex items-center gap-1.5 text-caption text-muted-foreground">
              {isPending ? (
                <>
                  <span className="size-1.5 shrink-0 animate-pulse rounded-full bg-muted-foreground" aria-hidden="true" />
                  Checking…
                </>
              ) : (
                <>
                  <span className="size-1.5 shrink-0 rounded-full bg-gain" aria-hidden="true" />
                  Ready
                </>
              )}
            </p>
          </div>
        </div>

        <p className="mt-3 text-label text-muted-foreground">
          {hasDocument
            ? "Ask questions about your uploaded documents."
            : "Ask questions about your uploaded documents."}
        </p>
      </header>

      {/* Fixed height so the composer stays anchored to the bottom of the card
          and long answers scroll internally instead of stretching the page. */}
      <div
        className={cn(
          "flex min-h-0 flex-1 flex-col px-3 pb-3",
          "[&>section]:rounded-xl [&>section]:border-0 [&>section]:bg-transparent [&>section]:shadow-none"
        )}
      >
        <ChatSurface
          key={documentId ?? "all-documents"}
          scope={documentId ? `document-${documentId}` : "documents"}
          documentId={documentId ?? undefined}
          inputLabel="Ask a research question about your documents"
          placeholder="Ask a question about your documents..."
          suggestions={RESEARCH_SUGGESTIONS}
          emptyTitle=""
          emptyDescription=""
          showCapabilities={false}
          variant="research"
        />
      </div>
    </section>
  );
}