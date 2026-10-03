"use client";

import { useRef, useState } from "react";
import { CheckCircle2, FileText, Loader2, Upload } from "lucide-react";

import { cn } from "@/lib/utils";

export type UploadState = "idle" | "uploading" | "success" | "error";

type Props = {
  state: UploadState;
  error: string;
  /** Receives the chosen/dropped file; validation and upload stay with the caller. */
  onFiles: (files: FileList | null) => void;
};

/**
 * Supported formats, kept honest against the backend.
 *
 * `app/ingestion/document_parser.py` declares `_SUPPORTED_EXTENSIONS = (".pdf",)`
 * and `document_service._validate_pdf` rejects anything else, so only PDF is
 * advertised here. Adding DOCX/TXT would promise a capability the API lacks.
 */
const SUPPORTED_FORMATS = [{ label: "PDF" }] as const;

/**
 * Upload panel.
 *
 * Owns only the file input and drag-hover state; the parent keeps ownership of
 * the upload mutation so the `["documents"]` query cache stays in one place.
 */
export function DocumentUploadCard({ state, error, onFiles }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const busy = state === "uploading";

  return (
    <section
      aria-labelledby="research-upload-heading"
      className="flex h-full flex-col rounded-2xl border border-border bg-card p-5 shadow-card"
    >
      <div className="min-w-0">
        <h2
          id="research-upload-heading"
          className="text-[1.125rem] font-semibold tracking-[-0.01em] text-foreground"
        >
          Upload financial documents
        </h2>
        <p className="mt-1 text-label text-muted-foreground">
          PDFs are parsed, chunked and indexed for retrieval. One file at a time.
        </p>
      </div>

      <input
        ref={inputRef}
        type="file"
        accept="application/pdf,.pdf"
        className="sr-only"
        aria-label="Choose a PDF document to upload"
        onChange={(event) => {
          void onFiles(event.target.files);
          // Reset so re-picking the same file fires `change` again.
          event.target.value = "";
        }}
      />

      <button
        type="button"
        disabled={busy}
        onClick={() => inputRef.current?.click()}
        onDragOver={(event) => {
          event.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(event) => {
          event.preventDefault();
          setDragOver(false);
          void onFiles(event.dataTransfer.files);
        }}
        aria-describedby="research-upload-formats"
        className={cn(
          "group mt-4 flex flex-1 flex-col items-center justify-center gap-3 rounded-2xl border border-dashed px-5 py-8 text-center",
          "transition-[background-color,border-color] duration-150",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          "disabled:cursor-progress",
          dragOver
            ? "border-brand bg-brand-subtle"
            : "border-border-strong bg-surface/40 hover:border-brand/50 hover:bg-brand-subtle/40"
        )}
      >
        {/* Decorative document illustration, drawn inline so no asset ships. */}
        <span className="relative" aria-hidden="true">
          <FileText size={40} strokeWidth={1.25} className="text-subtle-foreground/70" />
          <span className="absolute -bottom-1.5 left-1/2 flex size-6 -translate-x-1/2 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-soft">
            <Upload size={13} />
          </span>
        </span>

        <span className="mt-1 block text-[0.9375rem] font-semibold text-foreground">
          Upload financial documents
        </span>

        {busy ? (
          <span className="inline-flex items-center gap-2 text-label font-medium text-brand">
            <Loader2 size={14} className="motion-safe:animate-spin" aria-hidden="true" />
            Uploading and indexing…
          </span>
        ) : (
          <span className="flex flex-wrap items-center justify-center gap-2">
            <span
              className="pointer-events-none inline-flex h-10 items-center gap-2 rounded-xl bg-primary px-5 text-label font-medium text-primary-foreground shadow-soft transition-colors group-hover:bg-primary/90"
              aria-hidden="true"
            >
              <Upload size={15} />
              Choose a PDF file
            </span>
            <span className="text-label text-muted-foreground" aria-hidden="true">
              or drag and drop
            </span>
          </span>
        )}
      </button>

      <div id="research-upload-formats" className="mt-4 border-t border-border pt-3.5">
        <p className="text-caption font-medium text-subtle-foreground">
          Supported formats
        </p>
        <ul className="mt-2 flex flex-wrap items-center gap-x-5 gap-y-2">
          {SUPPORTED_FORMATS.map((format) => (
            <li
              key={format.label}
              className="inline-flex items-center gap-1.5 text-caption font-medium text-foreground"
            >
              <FileText size={13} className="text-loss" aria-hidden="true" />
              {format.label}
              <CheckCircle2 size={12} className="text-gain" aria-hidden="true" />
            </li>
          ))}
        </ul>
      </div>

      <div aria-live="polite" className="empty:mt-0">
        {state === "success" && (
          <p
            role="status"
            className="mt-3 inline-flex items-center gap-2 text-caption font-medium text-gain"
          >
            <CheckCircle2 size={14} aria-hidden="true" />
            Document indexed successfully.
          </p>
        )}

        {state === "error" && (
          <p role="alert" className="mt-3 text-caption font-medium text-loss">
            {error}
          </p>
        )}
      </div>
    </section>
  );
}