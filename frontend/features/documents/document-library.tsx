"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Check, FileText, Layers } from "lucide-react";

import { api } from "@/services/api";
import { useDocuments } from "@/hooks/use-documents";
import { cn } from "@/lib/utils";

import { DocumentSection } from "./document-section";
import {
  DocumentUploadCard,
  type UploadState,
} from "./document-upload-card";
import { ResearchAssistant } from "./research-assistant";

/**
 * Research workspace.
 *
 * Owns the upload/delete mutations and the "currently grounded" document id;
 * rendering is delegated to the presentational pieces. Data flows through the
 * shared `["documents"]` query key, so every document surface reads one cache
 * entry.
 *
 * Layout: a narrow 320px management column (upload + documents) beside a chat
 * panel that takes the remaining width and the full viewport height.
 */
export function DocumentLibrary() {
  const queryClient = useQueryClient();
  const { documents } = useDocuments();

  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [uploadError, setUploadError] = useState("");
  // `null` means "all documents" — the same value handed to the chat as
  // `documentId` (undefined there means no document filter).
  const [selectedId, setSelectedId] = useState<string | null>(null);

  const uploadMutation = useMutation({
    mutationFn: api.uploadDocument,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: api.deleteDocument,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  const activeId = selectedId;
  const activeDocument =
    documents.find((doc) => doc.document_id === activeId) ?? null;

  async function handleFiles(files: FileList | null) {
    if (!files || files.length === 0) return;

    const file = files[0];
    const isPdf =
      file.type === "application/pdf" || file.name.toLowerCase().endsWith(".pdf");

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
    <div className="grid min-h-0 gap-4 lg:grid-cols-[320px_minmax(0,1fr)] lg:gap-5">
      {/* Management column. It scrolls on its own once the library outgrows the
          viewport; the chat panel beside it never scrolls as a whole. */}
      <aside className="min-h-0 space-y-4 lg:overflow-y-auto lg:pr-1 lg:pb-1">
        <DocumentUploadCard
          state={uploadState}
          error={uploadError}
          onFiles={handleFiles}
        />

        <DocumentSection
          selectedId={activeId}
          onSelect={setSelectedId}
          onDelete={handleDelete}
          isDeleting={deleteMutation.isPending}
          deleteError={deleteMutation.isError ? deleteMutation.error : null}
        />
      </aside>

      <div className="h-[clamp(30rem,68vh,44rem)] min-h-[30rem] lg:h-full">
        <ResearchAssistant
          documentId={activeId}
          hasDocument={documents.length > 0}
          scopeControl={
            <DocumentScopeControl
              scopeLabel={activeDocument ? activeDocument.filename : null}
              onClear={() => setSelectedId(null)}
            />
          }
        />
      </div>
    </div>
  );
}

/**
 * Composer scope indicator. Read-only while scoped to "all"; clicking widens the
 * scope back to the whole library, so it doubles as the way out of a narrowed
 * scope without hunting for the sidebar row.
 */
function DocumentScopeControl({
  scopeLabel,
  onClear,
}: {
  scopeLabel: string | null;
  onClear: () => void;
}) {
  const Icon = scopeLabel ? FileText : Layers;

  return (
    <button
      type="button"
      onClick={scopeLabel ? onClear : undefined}
      disabled={!scopeLabel}
      title={scopeLabel ? `Scoped to ${scopeLabel}` : "Searching all documents"}
      aria-label={
        scopeLabel
          ? `Searching ${scopeLabel} only. Activate to search all documents.`
          : "Searching all documents"
      }
      className={cn(
        "inline-flex min-w-0 max-w-[16rem] items-center gap-1.5 rounded-lg border border-border bg-surface px-2 py-1 text-caption text-muted-foreground",
        "transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        scopeLabel
          ? "hover:border-border-strong hover:text-foreground"
          : "cursor-default"
      )}
    >
      <Icon size={12} className="shrink-0 text-subtle-foreground" aria-hidden="true" />
      <span className="truncate">
        {scopeLabel ?? "All documents"}
      </span>
      {scopeLabel && (
        <Check size={11} className="shrink-0 text-brand" aria-hidden="true" />
      )}
    </button>
  );
}