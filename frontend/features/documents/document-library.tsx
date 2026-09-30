"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  CloudUpload,
  Database,
  FileText,
  Loader2,
  Search,
  Trash2,
} from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ChatSurface } from "@/components/ui/chat-surface";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorDisplay } from "@/components/ui/error-display";
import { SkeletonList } from "@/components/ui/skeleton";
import { SectionHeading } from "@/components/ui/page-header";
import { api } from "@/services/api";
import { cn } from "@/lib/utils";
import type { DocumentData } from "@/types/analysis";

type UploadState = "idle" | "uploading" | "success" | "error";

/**
 * Example questions shown in the copilot's empty state. Clicking one sends it
 * through the existing chat path - no new backend behaviour.
 */
const RESEARCH_SUGGESTIONS = [
  "What were the key risks disclosed in this filing?",
  "Summarise management commentary and outlook.",
  "What was the financial performance reported?",
  "Which risks or uncertainties stand out?",
];

function formatSizeLabel(pages: number, chunks: number): string {
  return `${pages} ${pages === 1 ? "page" : "pages"} · ${chunks} ${
    chunks === 1 ? "chunk" : "chunks"
  }`;
}

function formatDate(value: string | null): string | null {
  if (!value) return null;

  const parsed = new Date(value);
  return Number.isNaN(parsed.getTime()) ? null : parsed.toLocaleDateString();
}

export function DocumentLibrary() {
  const queryClient = useQueryClient();

  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [uploadError, setUploadError] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);

  const documentsQuery = useQuery({
    queryKey: ["documents"],
    queryFn: () => api.listDocuments(),
  });

  const documents: DocumentData[] = documentsQuery.data?.data?.documents ?? [];

  const invalidateDocuments = () => {
    void queryClient.invalidateQueries({ queryKey: ["documents"] });
  };

  const uploadMutation = useMutation({
    mutationFn: api.uploadDocument,
    onSuccess: invalidateDocuments,
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteDocument,
    onSuccess: invalidateDocuments,
  });

  const selected =
    documents.find((doc) => doc.document_id === selectedId) ??
    documents[0] ??
    null;

  const activeId = selected?.document_id ?? null;

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;

    const file = files[0];
    const isPdf =
      file.type === "application/pdf" ||
      file.name.toLowerCase().endsWith(".pdf");

    if (!isPdf) {
      setUploadState("error");
      setUploadError("Only PDF documents are supported.");
      return;
    }

    setUploadState("uploading");
    setUploadError("");

    try {
      await uploadMutation.mutateAsync(file);
      setUploadState("success");
      window.setTimeout(() => setUploadState("idle"), 2000);
    } catch (err) {
      setUploadState("error");
      setUploadError(err instanceof Error ? err.message : "Upload failed.");
    }
  }

  async function handleDelete(documentId: string) {
    await deleteMutation.mutateAsync(documentId);

    if (activeId === documentId) {
      setSelectedId(null);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,5fr)_minmax(0,8fr)] lg:items-start">
      {/* Supporting column: documents. Sits second on small screens so the
          primary action (ask the AI) stays first on mobile. */}
      <div className="order-2 min-w-0 space-y-6 lg:order-1">
        <Card>
          <CardHeader>
            <div>
              <CardTitle as="h2">Upload a document</CardTitle>
              <p className="mt-1 text-label text-muted-foreground">
                PDFs are parsed, chunked and indexed for retrieval. One file at a
                time.
              </p>
            </div>
          </CardHeader>

          <CardBody>
            <input
              ref={inputRef}
              type="file"
              accept="application/pdf"
              className="sr-only"
              aria-label="Choose a PDF document to upload"
              onChange={(event) => {
                void handleFiles(event.target.files);
              }}
            />

            <button
              type="button"
              onClick={() => inputRef.current?.click()}
              onDragOver={(event) => {
                event.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(event) => {
                event.preventDefault();
                setDragOver(false);
                void handleFiles(event.dataTransfer.files);
              }}
              className={cn(
                "group flex w-full items-center gap-3.5 rounded-xl border border-dashed px-4 py-5 text-left",
                "transition-[background-color,border-color] duration-150",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                dragOver
                  ? "border-brand bg-brand-subtle"
                  : "border-border-strong bg-surface/50 hover:border-brand/50 hover:bg-brand-subtle/40"
              )}
            >
              {uploadState === "uploading" ? (
                <>
                  <Loader2
                    className="size-6 shrink-0 motion-safe:animate-spin text-brand"
                    aria-hidden="true"
                  />
                  <span className="min-w-0">
                    <span className="block text-label font-medium text-foreground">
                      Uploading and indexing…
                    </span>
                    <span className="mt-0.5 block text-caption text-muted-foreground">
                      Large filings can take a moment to embed.
                    </span>
                  </span>
                </>
              ) : (
                <>
                  <CloudUpload
                    className="size-6 shrink-0 text-brand transition-transform duration-150 group-hover:-translate-y-0.5"
                    aria-hidden="true"
                  />
                  <span className="min-w-0 flex-1">
                    <span className="block text-label font-medium text-foreground">
                      Upload a PDF
                    </span>
                    <span className="mt-0.5 block text-caption text-muted-foreground">
                      Drop it here or click to browse
                    </span>
                  </span>
                  <span className="shrink-0 rounded-full border border-border bg-card px-2 py-0.5 font-mono text-[11px] text-subtle-foreground">
                    PDF only
                  </span>
                </>
              )}
            </button>

            <div aria-live="polite" className="mt-3 empty:mt-0">
              {uploadState === "success" && (
                <p
                  role="status"
                  className="flex items-center justify-center gap-2 text-caption font-medium text-gain"
                >
                  <CheckCircle2 size={14} aria-hidden="true" />
                  Document indexed successfully.
                </p>
              )}

              {uploadState === "error" && (
                <p
                  role="alert"
                  className="text-center text-caption font-medium text-loss"
                >
                  {uploadError}
                </p>
              )}
            </div>
          </CardBody>
        </Card>

        <section aria-labelledby="library-heading" className="space-y-4">
          <SectionHeading
            id="library-heading"
            title="Document library"
            description={`${
              documentsQuery.isPending
                ? "Loading…"
                : `${documents.length} indexed ${
                    documents.length === 1 ? "document" : "documents"
                  }`
            }`}
            actions={
              <Button
                variant="secondary"
                size="sm"
                onClick={() =>
                  void queryClient.invalidateQueries({ queryKey: ["documents"] })
                }
              >
                Refresh
              </Button>
            }
          />

          {documentsQuery.isPending && (
            <div role="status" aria-busy="true">
              <SkeletonList items={3} />
              <span className="sr-only">Loading documents…</span>
            </div>
          )}

          {documentsQuery.isError && (
            <ErrorDisplay
              error={documentsQuery.error}
              onRetry={() => void documentsQuery.refetch()}
              title="Documents unavailable"
              compact
            />
          )}

          {!documentsQuery.isPending &&
            !documentsQuery.isError &&
            documents.length === 0 && (
              <EmptyState
                tone="brand"
                icon={<FileText size={20} aria-hidden="true" />}
                title="No documents uploaded yet"
                description="Upload a PDF above to build the knowledge base the AI agent retrieves from."
              />
            )}

          {documents.length > 0 && (
            <ul className="divide-y divide-border overflow-hidden rounded-xl border border-border bg-card">
              {documents.map((doc) => {
                const active = doc.document_id === activeId;
                const created = formatDate(doc.created_at);

                return (
                  <li
                    key={doc.document_id}
                    className={cn(
                      "flex items-center gap-3 px-4 py-3 transition-colors",
                      active ? "bg-brand-subtle/50" : "hover:bg-surface"
                    )}
                  >
                    <button
                      type="button"
                      onClick={() => setSelectedId(doc.document_id)}
                      aria-pressed={active}
                      className="flex min-w-0 flex-1 items-center gap-3 rounded-lg text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      <span
                        className={cn(
                          "flex size-9 shrink-0 items-center justify-center rounded-lg",
                          active
                            ? "bg-brand-subtle text-brand"
                            : "bg-muted text-muted-foreground"
                        )}
                      >
                        <FileText size={17} aria-hidden="true" />
                      </span>

                      <span className="min-w-0">
                        <span className="block truncate text-label font-medium text-foreground">
                          {doc.filename}
                        </span>
                        <span className="mt-0.5 block truncate text-caption text-muted-foreground">
                          {formatSizeLabel(doc.pages, doc.chunks)}
                          {created ? ` · ${created}` : ""}
                        </span>
                      </span>
                    </button>

                    <StatusBadge status={doc.status} />

                    <Button
                      variant="ghost"
                      size="icon-sm"
                      aria-label={`Delete ${doc.filename}`}
                      disabled={deleteMutation.isPending}
                      onClick={() => {
                        void handleDelete(doc.document_id);
                      }}
                    >
                      <Trash2 size={16} aria-hidden="true" />
                    </Button>
                  </li>
                );
              })}
            </ul>
          )}

          {deleteMutation.isError && (
            <ErrorDisplay
              error={deleteMutation.error}
              title="Delete failed"
              compact
            />
          )}
        </section>
      </div>

      {/* Primary column: the AI research copilot. */}
      <aside className="order-1 min-w-0 space-y-3 lg:order-2">
        {/* Knowledge context: makes DOCUMENT -> KNOWLEDGE BASE -> CHAT obvious.
            Rendered from the real document list - nothing is hardcoded. */}
        <div className="flex flex-wrap items-center gap-x-3 gap-y-2 rounded-xl border border-border bg-card px-3.5 py-2.5">
          <span className="flex shrink-0 items-center gap-1.5 text-[11px] font-semibold uppercase tracking-[0.12em] text-subtle-foreground">
            <Database size={12} aria-hidden="true" />
            Knowledge context
          </span>

          {documentsQuery.isPending ? (
            <span className="text-caption text-muted-foreground">Checking…</span>
          ) : documents.length === 0 ? (
            <span className="text-caption text-muted-foreground">
              No documents indexed yet — upload a PDF to ground the assistant.
            </span>
          ) : (
            <>
              <span
                className="text-caption text-muted-foreground"
                aria-live="polite"
              >
                {documents.length === 1
                  ? "Grounded in 1 document"
                  : `Grounded in ${documents.length} documents`}
              </span>
              <ul className="flex min-w-0 flex-wrap items-center gap-1.5">
                {documents.slice(0, 3).map((doc) => (
                  <li key={doc.document_id}>
                    <span
                      className={cn(
                        "inline-flex max-w-[14rem] items-center gap-1.5 rounded-md border px-2 py-0.5 text-caption",
                        activeId === doc.document_id
                          ? "border-brand/40 bg-brand-subtle text-brand"
                          : "border-border bg-surface text-muted-foreground"
                      )}
                    >
                      <span
                        className="size-1.5 shrink-0 rounded-full bg-gain"
                        aria-hidden="true"
                      />
                      <span className="truncate">{doc.filename}</span>
                      <span className="tnum shrink-0 text-subtle-foreground">
                        {formatSizeLabel(doc.pages, doc.chunks)}
                      </span>
                    </span>
                  </li>
                ))}
                {documents.length > 3 && (
                  <li className="text-caption text-subtle-foreground">
                    +{documents.length - 3} more
                  </li>
                )}
              </ul>
            </>
          )}

          <Link
            href="/search"
            className="ml-auto inline-flex shrink-0 items-center gap-1.5 text-caption font-medium text-brand underline-offset-4 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Search size={13} aria-hidden="true" />
            Direct search
          </Link>
        </div>

        {/* Fixed-height workspace so the composer is always pinned to the
            bottom of the panel and long answers scroll inside the conversation
            instead of stretching the page. `flex` makes the surface stretch to
            the wrapper (a block child would size to its content instead).
            The height is viewport-aware so the composer stays visible on
            typical laptop screens, clamped to a sensible range. */}
        <div className="flex h-[clamp(29rem,calc(100vh-22rem),40rem)] min-h-[29rem]">
          <ChatSurface
            key={activeId ?? "no-document"}
            scope={activeId ? `document-${activeId}` : "documents"}
            documentId={activeId ?? undefined}
            inputLabel="Ask a research question about your documents"
            placeholder={
              selected
                ? "Ask about this document…"
                : "Ask about your indexed documents…"
            }
            suggestions={RESEARCH_SUGGESTIONS}
            emptyTitle="Ask about your documents"
            emptyDescription="Ask questions about financial filings, management commentary, financial performance, risks, or other indexed research."
          />
        </div>
      </aside>
    </div>
  );
}
