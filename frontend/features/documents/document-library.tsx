"use client";

import { useRef, useState } from "react";
import { CloudUpload, FileText, Loader2, Trash2 } from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ChatSurface } from "@/components/ui/chat-surface";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";
import { StatusBadge } from "@/components/ui/badge";
import { EmptyState } from "@/components/ui/empty-state";
import { ErrorDisplay } from "@/components/ui/error-display";
import { SkeletonList } from "@/components/ui/skeleton";
import { api } from "@/services/api";
import type { DocumentData } from "@/types/analysis";

type UploadState = "idle" | "uploading" | "processing" | "success" | "error";

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
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div>
            <CardTitle as="h2">Upload a document</CardTitle>
            <p className="mt-1 text-label text-muted-foreground">
              Financial PDFs are parsed, chunked and indexed for retrieval.
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
            className={`flex h-40 w-full flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring ${
              dragOver
                ? "border-brand bg-brand-subtle"
                : "border-border bg-background hover:border-border-strong"
            }`}
          >
            {uploadState === "uploading" ? (
              <>
                <Loader2
                  className="motion-safe:animate-spin text-brand"
                  size={28}
                  aria-hidden="true"
                />
                <span className="text-label text-muted-foreground">
                  Uploading…
                </span>
              </>
            ) : (
              <>
                <CloudUpload className="text-brand" size={30} aria-hidden="true" />
                <span className="text-label text-foreground">
                  Drop a PDF here or click to browse
                </span>
                <span className="text-caption text-muted-foreground">
                  Financial reports, 10-K filings, earnings releases
                </span>
              </>
            )}
          </button>

          {uploadState === "success" && (
            <p role="status" className="mt-3 text-center text-caption text-gain">
              Document indexed successfully.
            </p>
          )}

          {uploadState === "error" && (
            <p role="alert" className="mt-3 text-center text-caption text-loss">
              {uploadError}
            </p>
          )}
        </CardBody>
      </Card>

      <div className="grid gap-6 xl:grid-cols-2">
        {/* Library */}
        <Card aria-labelledby="library-heading">
          <CardHeader>
            <div>
              <CardTitle as="h2" id="library-heading">
                Document library
              </CardTitle>
              <p className="mt-1 text-caption text-subtle-foreground">
                {documents.length} indexed document
                {documents.length === 1 ? "" : "s"}
              </p>
            </div>
          </CardHeader>

          <CardBody>
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
                  icon={<FileText size={20} aria-hidden="true" />}
                  title="No documents uploaded yet"
                  description="Upload a PDF above to build the knowledge base the AI agent retrieves from."
                />
              )}

            <div className="space-y-2">
              {documents.map((doc) => {
                const active = doc.document_id === activeId;

                return (
                  <div
                    key={doc.document_id}
                    className={`flex items-center gap-3 rounded-lg border p-3 transition-colors ${
                      active
                        ? "border-brand/40 bg-brand-subtle"
                        : "border-border bg-background hover:bg-muted/50"
                    }`}
                  >
                    <button
                      type="button"
                      onClick={() => setSelectedId(doc.document_id)}
                      aria-pressed={active}
                      className="flex min-w-0 flex-1 items-center gap-3 rounded-md text-left focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                    >
                      <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-muted text-muted-foreground">
                        <FileText size={18} aria-hidden="true" />
                      </span>

                      <span className="min-w-0">
                        <span className="block truncate text-label font-medium text-foreground">
                          {doc.filename}
                        </span>
                        <span className="mt-0.5 block text-caption text-muted-foreground">
                          {doc.pages} pages · {doc.chunks} chunks
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
                  </div>
                );
              })}
            </div>

            {deleteMutation.isError && (
              <div className="mt-3">
                <ErrorDisplay
                  error={deleteMutation.error}
                  title="Delete failed"
                  compact
                />
              </div>
            )}
          </CardBody>
        </Card>

        {/* Ask AI — shared chat surface (streaming, session, citations) */}
        <div className="min-h-0">
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
      </div>
    </div>
  );
}
