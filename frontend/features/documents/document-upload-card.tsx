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
 * Compact upload card for the Research sidebar.
 *
 * Owns only the file input and drag-hover state; the parent keeps ownership of
 * the upload mutation so the `["documents"]` query cache stays in one place.
 * The whole drop zone is a real `<button>`, so it is reachable by keyboard and
 * announced as a single control.
 */
export function DocumentUploadCard({ state, error, onFiles }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);

  const busy = state === "uploading";

  return (
    <section
      aria-labelledby="research-upload-heading"
      className="rounded-2xl border border-border bg-card p-4 shadow-card"
    >
      <h2
        id="research-upload-heading"
        className="text-label font-semibold tracking-[-0.005em] text-foreground"
      >
        Upload documents
      </h2>
      <p className="mt-1 text-caption text-muted-foreground">
        PDFs are parsed, chunked, and indexed.
      </p>

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
          "group mt-3 flex w-full flex-col items-center gap-2 rounded-xl border border-dashed px-3 py-4 text-center",
          "transition-[background-color,border-color] duration-150",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          "disabled:cursor-progress",
          dragOver
            ? "border-brand bg-brand-subtle"
            : "border-border-strong bg-surface/40 hover:border-brand/50 hover:bg-brand-subtle/40"
        )}
      >
        {/* Decorative document icon, drawn inline so no asset ships. */}
        <span
          className="flex size-9 items-center justify-center rounded-lg bg-brand-subtle text-brand ring-1 ring-brand/15"
          aria-hidden="true"
        >
          <FileText size={17} strokeWidth={1.5} />
        </span>

        <span className="text-caption font-semibold text-foreground">
          {busy ? "Uploading and indexing…" : "Drag and drop a PDF"}
        </span>

        {busy ? (
          <span
            className="inline-flex items-center gap-2 text-caption font-medium text-brand"
            role="status"
          >
            <Loader2
              size={13}
              className="motion-safe:animate-spin"
              aria-hidden="true"
            />
            Parsing and indexing…
          </span>
        ) : (
          <span
            className="pointer-events-none inline-flex h-8 items-center gap-1.5 rounded-lg bg-primary px-3 text-caption font-medium text-primary-foreground shadow-soft transition-colors group-hover:bg-primary/90"
            aria-hidden="true"
          >
            <Upload size={13} />
            Choose file
          </span>
        )}
      </button>

      <p id="research-upload-formats" className="mt-2.5 text-caption text-subtle-foreground">
        {SUPPORTED_FORMATS.map((format) => format.label).join(", ")} only · one file
        at a time
      </p>

      <div aria-live="polite" className="empty:mt-0">
        {state === "success" && (
          <p
            role="status"
            className="mt-2.5 inline-flex items-center gap-1.5 text-caption font-medium text-gain"
          >
            <CheckCircle2 size={13} aria-hidden="true" />
            Document indexed successfully.
          </p>
        )}

        {state === "error" && (
          <p role="alert" className="mt-2.5 text-caption font-medium text-loss">
            {error}
          </p>
        )}
      </div>
    </section>
  );
}