"use client";

import { useRef, useState } from "react";
import {
  CloudUpload,
  FileText,
  Loader2,
  Trash2,
  BookOpen,
} from "lucide-react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { ChatSurface } from "@/components/ui/chat-surface";
import { GlassCard } from "@/components/ui/glass-card";
import { api } from "@/services/api";
import type { DocumentData } from "@/types/analysis";

type UploadState =
  | "idle"
  | "uploading"
  | "processing"
  | "success"
  | "error";

export function DocumentLibrary() {
  const queryClient = useQueryClient();

  const [uploadState, setUploadState] =
    useState<UploadState>("idle");

  const [uploadError, setUploadError] = useState("");

  const [dragOver, setDragOver] = useState(false);

  const [selectedId, setSelectedId] = useState<
    string | null
  >(null);

  const inputRef = useRef<HTMLInputElement>(null);

  const documentsQuery = useQuery({
    queryKey: ["documents"],
    queryFn: () => api.listDocuments(),
  });

  const documents: DocumentData[] =
    documentsQuery.data?.data?.documents ?? [];

  const invalidateDocuments = () => {
    queryClient.invalidateQueries({
      queryKey: ["documents"],
    });
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
    documents.find(
      (doc) => doc.document_id === selectedId
    ) ??
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

      setSelectedId((current) => current ?? null);

      setUploadState("success");

      setTimeout(() => setUploadState("idle"), 2000);
    } catch (err) {
      setUploadState("error");

      setUploadError(
        err instanceof Error ? err.message : "Upload failed."
      );
    }
  }

  async function handleDelete(documentId: string) {
    await deleteMutation.mutateAsync(documentId);

    if (activeId === documentId) {
      setSelectedId(null);
    }
  }

  return (
    <div className="space-y-8">
      <header>
        <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-2 text-sm text-blue-300">
          <BookOpen size={16} />
          Document Research
        </div>

        <h1 className="mt-6 text-4xl font-bold text-white">
          Financial Document Intelligence
        </h1>

        <p className="mt-3 max-w-2xl text-zinc-400">
          Upload a financial PDF — it is parsed, chunked, embedded
          and indexed for retrieval. Then ask grounded questions
          with page-level citations.
        </p>
      </header>

      {/* Upload */}
      <GlassCard glow className="p-8">
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />

        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            handleFiles(e.dataTransfer.files);
          }}
          className={`flex h-44 w-full flex-col items-center justify-center gap-3 rounded-3xl border-2 border-dashed transition-colors ${
            dragOver
              ? "border-blue-400 bg-blue-500/10"
              : "border-white/10 bg-white/[0.02] hover:border-blue-400/40"
          }`}
        >
          {uploadState === "uploading" ? (
            <>
              <Loader2 className="animate-spin text-blue-400" size={32} />
              <span className="text-zinc-300">Uploading…</span>
            </>
          ) : uploadState === "processing" ? (
            <>
              <Loader2 className="animate-spin text-blue-400" size={32} />
              <span className="text-zinc-300">Indexing document…</span>
            </>
          ) : (
            <>
              <CloudUpload className="text-blue-400" size={36} />
              <span className="text-lg text-zinc-300">
                Drop a PDF here or click to browse
              </span>
              <span className="text-sm text-zinc-500">
                Financial reports, 10-K filings, earnings releases
              </span>
            </>
          )}
        </button>

        {uploadState === "success" && (
          <p className="mt-4 text-center text-sm text-emerald-400">
            Document indexed successfully.
          </p>
        )}

        {uploadState === "error" && (
          <p className="mt-4 text-center text-sm text-red-400">
            {uploadError}
          </p>
        )}
      </GlassCard>

      <div className="grid gap-8 xl:grid-cols-2">
        {/* Library */}
        <GlassCard className="p-6">
          <h2 className="text-xl font-semibold text-white">
            Document Library
          </h2>

          <p className="mt-1 text-sm text-zinc-500">
            {documents.length} indexed document(s)
          </p>

          <div className="mt-6 space-y-3">
            {documentsQuery.isLoading && (
              <div className="flex items-center justify-center gap-2 rounded-2xl border border-white/5 bg-white/[0.02] p-6 text-sm text-zinc-500">
                <Loader2 className="h-4 w-4 animate-spin" />
                Loading documents…
              </div>
            )}

            {!documentsQuery.isLoading && documents.length === 0 && (
              <p className="rounded-2xl border border-white/5 bg-white/[0.02] p-6 text-center text-sm text-zinc-500">
                No documents uploaded yet.
              </p>
            )}

            {documents.map((doc) => {
              const active = doc.document_id === activeId;

              return (
                <div
                  key={doc.document_id}
                  onClick={() => {
                    setSelectedId(doc.document_id);
                  }}
                  className={`flex cursor-pointer items-center gap-4 rounded-2xl border p-4 transition-colors ${
                    active
                      ? "border-blue-400/40 bg-blue-500/10"
                      : "border-white/5 bg-white/[0.02] hover:bg-white/[0.05]"
                  }`}
                >
                  <div className="rounded-xl bg-white/5 p-3">
                    <FileText
                      className={active ? "text-blue-300" : "text-zinc-400"}
                      size={22}
                    />
                  </div>

                  <div className="min-w-0 flex-1">
                    <p className="truncate font-medium text-white">
                      {doc.filename}
                    </p>

                    <p className="mt-1 text-sm text-zinc-500">
                      {doc.pages} pages · {doc.chunks} chunks · {doc.status}
                    </p>
                  </div>

                  <button
                    type="button"
                    aria-label={`Delete ${doc.filename}`}
                    disabled={deleteMutation.isPending}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleDelete(doc.document_id);
                    }}
                    className="rounded-xl border border-white/10 p-2 text-zinc-400 transition-colors hover:border-red-400/40 hover:text-red-400 disabled:opacity-50"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              );
            })}
          </div>
        </GlassCard>

        {/* Ask AI — shared chat surface (streaming, session, citations) */}
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
  );
}
