"use client";

import { useRef, useState } from "react";
import Link from "next/link";
import {
  CheckCircle2,
  CloudUpload,
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
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_26rem] xl:items-start">
      <div className="min-w-0 space-y-6">
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
                "group flex w-full flex-col items-center justify-center gap-2 rounded-xl border border-dashed px-6 py-10 text-center",
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
                    className="motion-safe:animate-spin text-brand"
                    size={26}
                    aria-hidden="true"
                  />
                  <span className="text-label font-medium text-foreground">
                    Uploading and indexing…
                  </span>
                  <span className="text-caption text-muted-foreground">
                    Large filings can take a moment to embed.
                  </span>
                </>
              ) : (
                <>
                  <CloudUpload
                    className="text-brand transition-transform duration-150 group-hover:-translate-y-0.5"
                    size={26}
                    aria-hidden="true"
                  />
                  <span className="text-label font-medium text-foreground">
                    Drop a PDF here or click to browse
                  </span>
                  <span className="text-caption text-muted-foreground">
                    10-K filings, annual reports, earnings releases
                  </span>
                  <span className="mt-1 rounded-full border border-border bg-card px-2.5 py-0.5 font-mono text-[11px] text-subtle-foreground">
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

      <aside className="min-w-0 space-y-4 xl:sticky xl:top-24">
        <div className="flex items-center justify-between gap-3">
          <h2 className="text-subtitle text-foreground">Ask the copilot</h2>
          <Link
            href="/search"
            className="inline-flex items-center gap-1.5 text-caption font-medium text-brand underline-offset-4 hover:underline"
          >
            <Search size={13} aria-hidden="true" />
            Direct search
          </Link>
        </div>

        <p className="text-caption text-muted-foreground">
          {selected
            ? `Grounded in ${selected.filename}.`
            : "Upload a document to ground the copilot in your filings."}
        </p>

        <div className="h-[30rem]">
          <ChatSurface
            key={activeId ?? "no-document"}
            scope={activeId ? `document-${activeId}` : "documents"}
            documentId={activeId ?? undefined}
            inputLabel="Ask a question about the selected document"
            placeholder={
              selected
                ? "e.g. What did management say about AI infrastructure spending?"
                : "Upload a document first."
            }
          />
        </div>
      </aside>
    </div>
  );
}
