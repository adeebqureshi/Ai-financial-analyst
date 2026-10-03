"use client";

import { useMemo, useState } from "react";
import {
  FileText,
  LayoutGrid,
  List,
  MessageSquare,
  RefreshCw,
  Search,
  Trash2,
} from "lucide-react";

import { StatusBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorDisplay } from "@/components/ui/error-display";
import { Input } from "@/components/ui/field";
import { SkeletonList } from "@/components/ui/skeleton";
import { formatDocumentExtent, useDocuments } from "@/hooks/use-documents";
import { cn } from "@/lib/utils";
import type { DocumentData } from "@/types/analysis";

type ViewMode = "list" | "grid";

function formatDate(value: string | null): string | null {
  if (!value) return null;

  const parsed = new Date(value);

  return Number.isNaN(parsed.getTime())
    ? null
    : parsed.toLocaleString(undefined, {
        day: "numeric",
        month: "short",
        year: "numeric",
        hour: "numeric",
        minute: "2-digit",
      });
}

type Props = {
  /** Currently grounded document; selecting a row scopes the assistant to it. */
  selectedId: string | null;
  onSelect: (documentId: string) => void;
  onDelete: (documentId: string) => void;
  isDeleting: boolean;
  deleteError: unknown;
};

/**
 * "Your Documents" — count, toolbar and rows.
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
  const [statusFilter, setStatusFilter] = useState<"all" | "indexed">("all");
  const [view, setView] = useState<ViewMode>("list");

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase();

    return documents.filter((doc) => {
      if (statusFilter === "indexed" && doc.status !== "indexed") return false;
      if (!needle) return true;

      return doc.filename.toLowerCase().includes(needle);
    });
  }, [documents, query, statusFilter]);

  // A failed or throttled request means the count is *unknown*, not zero. The
  // `useDocuments` hook deliberately keeps `total` nullable for this reason, so
  // the label must not contradict it by rendering "0 documents" while the
  // throttle/error notice is on screen.
  const countLabel = isPending
    ? "Loading…"
    : isError
      ? "Unavailable"
      : `${documents.length} ${documents.length === 1 ? "document" : "documents"}`;

  return (
    <section aria-labelledby="library-heading" className="space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-x-6 gap-y-3">
        <div className="flex min-w-0 items-baseline gap-2.5">
          <h2
            id="library-heading"
            className="text-[1.25rem] font-semibold tracking-[-0.015em] text-foreground"
          >
            Your Documents
          </h2>
          <span className="tnum shrink-0 text-caption text-muted-foreground">
            {countLabel}
          </span>
        </div>

        <DocumentToolbar
          query={query}
          onQueryChange={setQuery}
          statusFilter={statusFilter}
          onStatusFilterChange={setStatusFilter}
          view={view}
          onViewChange={setView}
          onRefresh={() => void refetch()}
          isRefreshing={isPending}
        />
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
            className="rounded-xl border border-warning/25 bg-warning-subtle px-4 py-3 text-caption text-warning"
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
        <EmptyState
          tone="brand"
          icon={<FileText size={20} aria-hidden="true" />}
          title="No documents yet"
          description="Upload a financial document to build your searchable knowledge base."
        />
      )}

      {!isPending && !isError && documents.length > 0 && filtered.length === 0 && (
        <EmptyState
          compact
          title="No documents match"
          description="Adjust the search text or status filter to see more of your library."
        />
      )}

      {filtered.length > 0 && (
        <ul
          className={cn(
            view === "list" ? "space-y-2" : "grid gap-3 sm:grid-cols-2 xl:grid-cols-3"
          )}
        >
{filtered.map((doc) => (
            <DocumentRow
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

function DocumentToolbar({
  query,
  onQueryChange,
  statusFilter,
  onStatusFilterChange,
  view,
  onViewChange,
  onRefresh,
  isRefreshing,
}: {
  query: string;
  onQueryChange: (value: string) => void;
  statusFilter: "all" | "indexed";
  onStatusFilterChange: (value: "all" | "indexed") => void;
  view: ViewMode;
  onViewChange: (value: ViewMode) => void;
  onRefresh: () => void;
  isRefreshing: boolean;
}) {
  return (
    <div className="flex min-w-0 flex-wrap items-center gap-2">
      <div className="relative min-w-0 flex-1 sm:flex-none">
        <Search
          size={14}
          className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-subtle-foreground"
          aria-hidden="true"
        />
        <Input
          type="search"
          value={query}
          onChange={(event) => onQueryChange(event.target.value)}
          placeholder="Search documents..."
          aria-label="Search documents by filename"
          className="h-9 w-full pl-8 text-caption sm:w-56"
        />
      </div>

      <div className="flex shrink-0 items-center gap-1.5">
        <label htmlFor="document-status-filter" className="sr-only">
          Filter documents by status
        </label>
        <select
          id="document-status-filter"
          value={statusFilter}
          onChange={(event) =>
            onStatusFilterChange(event.target.value as "all" | "indexed")
          }
          className="h-9 rounded-lg border border-border bg-card px-2.5 text-caption text-foreground transition-colors hover:border-border-strong focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
        >
          <option value="all">All</option>
          <option value="indexed">Indexed</option>
        </select>

        <Button
          type="button"
          variant="secondary"
          size="icon-sm"
          onClick={onRefresh}
          aria-label="Refresh document library"
          disabled={isRefreshing}
        >
          <RefreshCw
            size={14}
            className={cn(isRefreshing && "motion-safe:animate-spin")}
            aria-hidden="true"
          />
        </Button>

        <div
          role="group"
          aria-label="Document view"
          className="flex items-center gap-0.5 rounded-lg border border-border bg-card p-0.5"
        >
          <ViewToggleButton
            active={view === "grid"}
            label="Grid view"
            onClick={() => onViewChange("grid")}
          >
            <LayoutGrid size={14} aria-hidden="true" />
          </ViewToggleButton>
          <ViewToggleButton
            active={view === "list"}
            label="List view"
            onClick={() => onViewChange("list")}
          >
            <List size={14} aria-hidden="true" />
          </ViewToggleButton>
        </div>
      </div>
    </div>
  );
}

function ViewToggleButton({
  active,
  label,
  onClick,
  children,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
  children: React.ReactNode;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-pressed={active}
      aria-label={label}
className={cn(
        "flex size-7 items-center justify-center rounded-md transition-colors",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        active
          ? "bg-brand-subtle text-brand"
          : "text-muted-foreground hover:bg-muted hover:text-foreground"
      )}
    >
      {children}
    </button>
  );
}

type RowProps = {
  doc: DocumentData;
  active: boolean;
  isDeleting: boolean;
  onSelect: (documentId: string) => void;
  onDelete: (documentId: string) => void;
};

function DocumentRow({
  doc,
  active,
  isDeleting,
  onSelect,
  onDelete,
}: RowProps) {
  const created = formatDate(doc.created_at);

  return (
    <li
      className={cn(
        "group flex items-center gap-3 rounded-2xl border bg-card px-3.5 py-3 transition-colors",
        active
          ? "border-brand/40 bg-brand-subtle/30"
          : "border-border hover:border-border-strong"
      )}
    >
      <button
        type="button"
        onClick={() => onSelect(doc.document_id)}
        aria-pressed={active}
        className="flex min-w-0 flex-1 items-center gap-3 rounded-xl text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
      >
        <span
          className={cn(
            "flex size-9 shrink-0 items-center justify-center rounded-xl",
            active ? "bg-brand-subtle text-brand" : "bg-muted text-muted-foreground"
          )}
          aria-hidden="true"
        >
          <FileText size={17} />
        </span>

        <span className="min-w-0">
          <span className="block truncate text-label font-semibold text-foreground">
            {doc.filename}
          </span>
          <span className="mt-0.5 flex flex-wrap items-center gap-x-2 text-caption text-muted-foreground">
            <span className="tnum">
              {formatDocumentExtent(doc.pages, doc.chunks)}
            </span>
            {created && (
              <>
                <span className="text-border-strong" aria-hidden="true">
                  ·
                </span>
                <span className="tnum">{created}</span>
              </>
            )}
          </span>
        </span>
      </button>

      <StatusBadge status={doc.status} />

      <div className="flex shrink-0 items-center gap-0.5">
        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          aria-label={`Ask the assistant about ${doc.filename}`}
          onClick={() => onSelect(doc.document_id)}
        >
          <MessageSquare size={15} aria-hidden="true" />
        </Button>

        <Button
          type="button"
          variant="ghost"
          size="icon-sm"
          aria-label={`Delete ${doc.filename}`}
          disabled={isDeleting}
          onClick={() => onDelete(doc.document_id)}
          className="hover:text-loss"
        >
          <Trash2 size={15} aria-hidden="true" />
        </Button>
      </div>
    </li>
  );
}
