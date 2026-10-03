"use client";

import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { api } from "@/services/api";
import { useDocuments } from "@/hooks/use-documents";

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
 */
export function DocumentLibrary() {
  const queryClient = useQueryClient();
  const { documents } = useDocuments();

  const [uploadState, setUploadState] = useState<UploadState>("idle");
  const [uploadError, setUploadError] = useState("");
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

  // Default to the newest document so the assistant is grounded on load.
  const activeId = selectedId ?? documents[0]?.document_id ?? null;

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
    <div className="space-y-6">
      {/* Primary workspace: upload and assistant have equal visual weight and
          share a row on desktop, stacking header→upload→assistant on mobile. */}
      <div className="grid items-stretch gap-5 lg:grid-cols-2">
        <DocumentUploadCard
          state={uploadState}
          error={uploadError}
          onFiles={handleFiles}
        />

        <div className="flex h-[clamp(26rem,calc(100vh-19rem),34rem)] min-h-[26rem]">
          <ResearchAssistant
            documentId={activeId}
            hasDocument={documents.length > 0}
          />
        </div>
      </div>

      <DocumentSection
        selectedId={activeId}
        onSelect={setSelectedId}
        onDelete={handleDelete}
        isDeleting={deleteMutation.isPending}
        deleteError={deleteMutation.isError ? deleteMutation.error : null}
      />
    </div>
  );
}
