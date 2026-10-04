"use client";

import { useMemo, useState } from "react";
import {
  Check,
  FileText,
  Layers,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";

import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ErrorDisplay } from "@/components/ui/error-display";
import { Input } from "@/components/ui/field";
import { SkeletonList } from "@/components/ui/skeleton";
import { formatDocumentExtent, useDocuments } from "@/hooks/use-documents";
import { cn } from "@/lib/utils";
import type { DocumentData } from "@/types/analysis";

type Props = {
  /**
   * Currently grounded document. `null` means the whole library is in scope —
   * the same value the assistant passes to the chat as `documentId`.
   */
  selectedId: string | null;
  /** Selecting `null` widens the scope back to every indexed document. */
  onSelect: (documentId: string | null) => void;
  onDelete: (documentId: string) => void;
  isDeleting: boolean;
  deleteError: unknown;
};

/**
 * "Your documents" — count, search and compact cards for the Research sidebar.
 *
 * Every field is read from the real `/documents` payload via the shared
 * `useDocuments` hook, which uses the same `["documents"]` key as the rest of
 * the workspace, so this adds no extra network traffic.
 */
export function DocumentSection({
  selectedId,
  onSelect,
  onDelete,
  isDeleting,
  deleteError,
}: Props) {
  const { documents, isPending, isError, error, isRateLimited, refetch } =
    useDocuments();

  const [query, setQuery] = useState("");

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();

    if (!needle) return documents;

    return documents.filter((doc) =>
      doc.filename.toLowerCase().includes(needle)
    );
  }, [documents, query]);

  // A failed or throttled request means the count is *unknown*, not zero. The
  // `useDocuments` hook deliberately keeps `total` nullable for this reason, so
  // the label must not contradict it by rendering "0" while the notice is up.
  const countLabel = isPending
    ? "Loading…"
    : isError
      ? "Unavailable"
      : documents.length;

  return (
    <section aria-labelledby="library-heading" className="space-y-2.5">
      <div className="flex items-center justify-between gap-3 px-0.5">
        <h2
          id="library-heading"
          className="text-label font-semibold tracking-[-0.005em] text-foreground"
        >
          Your documents
        </h2>
        <span className="tnum shrink-0 rounded-full border border-border bg-card px-2 py-0.5 text-caption text-muted-foreground">
          {countLabel}
        </span>
      </div>

      <div className="flex items-center gap-1.5">
        <div className="relative min-w-0 flex-1">
          <Search
            size={13}
            className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-subtle-foreground"
            aria-hidden="true"
          />
          <Input
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search documents"
            aria-label="Search documents by filename"
            className="h-8 w-full pl-8 text-caption"
          />
        </div>

        <Button
          type="button"
          variant="secondary"
          size="icon-sm"
          onClick={() => void refetch()}
          aria-label="Refresh document library"
          disabled={isPending}
        >
          <RefreshCw
            size={13}
            className={cn(isPending && "motion-safe:animate-spin")}
            aria-hidden="true"
          />
        </Button>
      </div>

      {isPending && (
        <div role="status" aria-busy="true">
          <SkeletonList items={3} />
          <span className="sr-only">Loading documents…</span>
        </div>
      )}

      {/* A throttled request is not an outage — the wording must not claim the
          service is down when the backend merely refused the call. */}
      {isError &&
        (isRateLimited ? (
          <p
            role="status"
            className="rounded-xl border border-warning/25 bg-warning-subtle px-3 py-2 text-caption text-warning"
          >
            Temporarily throttled — too many requests. Try again in a moment.
          </p>
        ) : (
          <ErrorDisplay
            error={error}
            onRetry={() => void refetch()}
            title="Documents unavailable"
            compact
          />
        ))}

      {!isPending && !isError && documents.length === 0 && (
        <p className="rounded-xl border border-dashed border-border-strong/70 bg-surface/40 px-3 py-4 text-center text-caption text-muted-foreground">
          No documents yet. Upload a PDF to build your knowledge base.
        </p>
      )}

      {!isPending && !isError && documents.length > 0 && filtered.length === 0 && (
        <p className="rounded-xl border border-dashed border-border-strong/70 bg-surface/40 px-3 py-4 text-center text-caption text-muted-foreground">
          No documents match “{query.trim()}”.
        </p>
      )}

      {!isPending && !isError && documents.length > 0 && (
        <ul className="space-y-1.5">
          {/* Explicit "all documents" scope, so narrowing to one file is always
              reversible without clearing the selection elsewhere. */}
          <li>
            <button
              type="button"
              onClick={() => onSelect(null)}
              aria-pressed={selectedId === null}
              className={cn(
                "flex w-full items-center gap-2.5 rounded-xl border px-2.5 py-2 text-left transition-colors",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                selectedId === null
                  ? "border-brand/40 bg-brand-subtle/40"
                  : "border-border bg-card hover:border-border-strong"
              )}
            >
              <span
                className={cn(
                  "flex size-7 shrink-0 items-center justify-center rounded-lg",
                  selectedId === null
                    ? "bg-brand-subtle text-brand"
                    : "bg-muted text-muted-foreground"
                )}
                aria-hidden="true"
              >
                <Layers size={14} />
              </span>

              <span className="min-w-0 flex-1 truncate text-caption font-medium text-foreground">
                All documents
              </span>

              {selectedId === null && (
                <Check size={13} className="shrink-0 text-brand" aria-hidden="true" />
              )}
            </button>
          </li>

          {filtered.map((doc) => (
            <DocumentCard
              key={doc.document_id}
              doc={doc}
              active={doc.document_id === selectedId}
              isDeleting={isDeleting}
              onSelect={onSelect}
              onDelete={onDelete}
            />
          ))}
        </ul>
      )}

      {deleteError != null && (
        <ErrorDisplay error={deleteError} title="Delete failed" compact />
      )}
    </section>
  );
}

type CardProps = {
  doc: DocumentData;
  active: boolean;
  isDeleting: boolean;
  onSelect: (documentId: string | null) => void;
  onDelete: (documentId: string) => void;
};

function DocumentCard({
  doc,
  active,
  isDeleting,
  onSelect,
  onDelete,
}: CardProps) {
  return (
    <li
      className={cn(
        "group flex items-start gap-2 rounded-xl border px-2.5 py-2 transition-colors",
        active
          ? "border-brand/40 bg-brand-subtle/30"
          : "border-border bg-card hover:border-border-strong"
      )}
    >
      <button
        type="button"
        onClick={() => onSelect(doc.document_id)}
        aria-pressed={active}
        aria-label={`Ask the assistant about ${doc.filename}`}
        title={doc.filename}
        className="flex min-w-0 flex-1 items-start gap-2.5 rounded-lg text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <span
          className={cn(
            "flex size-7 shrink-0 items-center justify-center rounded-lg",
            active ? "bg-brand-subtle text-brand" : "bg-muted text-muted-foreground"
          )}
          aria-hidden="true"
        >
          <FileText size={14} />
        </span>

        <span className="min-w-0 flex-1">
          <span className="block truncate text-caption font-semibold text-foreground">
            {doc.filename}
          </span>
          <span className="tnum mt-0.5 block truncate text-caption text-muted-foreground">
            {formatDocumentExtent(doc.pages, doc.chunks)}
          </span>
        </span>
      </button>

      <div className="flex shrink-0 flex-col items-end gap-1">
        <StatusBadge status={doc.status} />
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          aria-label={`Delete ${doc.filename}`}
          disabled={isDeleting}
          onClick={() => onDelete(doc.document_id)}
          className="size-7 hover:text-loss"
        >
          <Trash2 size={13} aria-hidden="true" />
        </Button>
      </div>
    </li>
  );
}