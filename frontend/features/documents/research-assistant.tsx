"use client";

import type { ReactNode } from "react";
import { Sparkles } from "lucide-react";

import { ChatSurface } from "@/components/ui/chat-surface";

import { useDocuments } from "@/hooks/use-documents";

/**
 * Example questions. Clicking one goes through `ChatSurface`'s existing `send()`
 * path, so suggestions hit the same RAG endpoint as a typed question — they are
 * not decorative.
 */
const RESEARCH_SUGGESTIONS = [
  "Summarize key risks",
  "Compare margins by segment",
  "List management guidance",
  "What drove revenue growth?",
];

type Props = {
  /** Document the assistant is grounded in; falls back to the whole library. */
  documentId: string | null;
  hasDocument: boolean;
  /** Document-scope switcher rendered at the bottom-left of the composer. */
  scopeControl?: ReactNode;
};

/**
 * Right-hand "AI Research Assistant" panel.
 *
 * Reuses `ChatSurface` (streaming, citations, retry, new-chat, sessions) rather
 * than reimplementing a second chat system — only the surrounding container and
 * the status/scope chrome are adapted to the reference layout.
 */
export function ResearchAssistant({
  documentId,
  hasDocument,
  scopeControl,
}: Props) {
  const { documents, isPending, isError } = useDocuments();

  const documentLabel = `${documents.length} ${
    documents.length === 1 ? "document" : "documents"
  }`;

  return (
    <section
      aria-labelledby="research-assistant-heading"
      className="flex h-full min-h-0 flex-col overflow-hidden rounded-2xl border border-border bg-card shadow-card"
    >
      <h2 id="research-assistant-heading" className="sr-only">
        AI Research Assistant
      </h2>

      {/* Fixed height (set by the page grid) so the composer stays anchored to
          the bottom of the panel and long answers scroll internally instead of
          stretching the page. */}
      <div className="flex min-h-0 flex-1 flex-col [&>section]:min-h-0">
        <ChatSurface
          key={documentId ?? "all-documents"}
          scope={documentId ? `document-${documentId}` : "documents"}
          documentId={documentId ?? undefined}
          inputLabel="Ask a research question about your documents"
          placeholder="Ask a question about your documents..."
          suggestions={RESEARCH_SUGGESTIONS}
          showCapabilities={false}
          variant="research"
          headerIcon={<Sparkles size={18} />}
          headerTitle="AI research assistant"
          headerMeta={hasDocument ? `· ${documentLabel}` : "· no documents yet"}
          statusPending={isPending}
          statusError={isError}
          scopeControl={scopeControl}
        />
      </div>
    </section>
  );
}