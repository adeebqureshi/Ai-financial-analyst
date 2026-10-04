"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Download, Loader2 } from "lucide-react";

import { api } from "@/services/api";
import { Button } from "@/components/ui/button";

import type { AnalysisPdfRequest } from "@/types/analysis";

type Props = {
  /** The completed analysis to render. Only ever set once data has loaded. */
  analysis: AnalysisPdfRequest;
};

/**
 * Turns the analysis already on screen into a downloadable PDF.
 *
 * Three states matter to the user: idle, working, and failed. The button is
 * disabled while a download is in flight so a double click cannot queue two
 * renders, and the error text is deliberately generic — the underlying
 * ApiError may carry an upstream message that means nothing to a reader.
 *
 * The caller keys this by ticker, so moving to another company remounts it and
 * no state needs to be reset by hand.
 */
export function DownloadReportButton({ analysis }: Props) {
  const [status, setStatus] = useState<"idle" | "working" | "error">("idle");
  const mounted = useRef(true);
  /**
   * Synchronous in-flight guard.
   *
   * `disabled` alone is not enough: React re-renders and disables the button
   * only after the first click has been handled, so clicks two and three of a
   * fast triple-click can still land and each start a render. This ref is set
   * before any await, so a second request cannot begin.
   */
  const inFlight = useRef(false);
  /**
   * Timestamp of the last completed render.
   *
   * Rendering is fast enough that a burst of clicks can straddle the end of one
   * download: the button re-enables, the next click lands, and the user ends up
   * with two copies of the same file. A short cooldown swallows that tail.
   */
  const lastFinished = useRef(0);
  const COOLDOWN_MS = 750;

  useEffect(() => {
    mounted.current = true;

    return () => {
      mounted.current = false;
    };
  }, []);

  const download = useCallback(async () => {
    if (inFlight.current) return;
    if (Date.now() - lastFinished.current < COOLDOWN_MS) return;

    inFlight.current = true;
    setStatus("working");

    let url: string | null = null;

    try {
      const { blob, filename } = await api.analysisPdf(analysis);

      // A zero-length or non-PDF body means the round trip failed in a way the
      // status code did not describe; treat it as a failure rather than
      // handing the user an unopenable file.
      if (blob.size === 0 || blob.type.indexOf("pdf") === -1) {
        throw new Error("The renderer did not return a PDF.");
      }

      const safeName =
        filename && filename.toLowerCase().endsWith(".pdf")
          ? filename
          : `${analysis.ticker}_Financial_Analysis_Report.pdf`;

      url = URL.createObjectURL(blob);

      const link = document.createElement("a");
      link.href = url;
      link.download = safeName;
      link.rel = "noopener";
      document.body.appendChild(link);
      link.click();
      link.remove();

      // Revoking immediately can cancel the download in some browsers, so the
      // URL is released on the next tick instead.
      window.setTimeout(() => {
        if (url) URL.revokeObjectURL(url);
      }, 0);

      if (mounted.current) setStatus("idle");
    } catch (error) {
      if (url) URL.revokeObjectURL(url);

      // Deliberately generic: the underlying ApiError may carry an upstream
      // message ("upstream provider failure", a 504 body) that means nothing to
      // the reader. The console keeps the detail for debugging.
      if (error instanceof Error) {
        console.error("[download-report] PDF generation failed", error);
      }

      if (mounted.current) setStatus("error");
    } finally {
      inFlight.current = false;
      lastFinished.current = Date.now();
    }
  }, [analysis]);

  const working = status === "working";

  return (
    <div className="space-y-1.5">
      <Button
        type="button"
        variant="secondary"
        size="sm"
        onClick={() => void download()}
        disabled={working}
        aria-busy={working}
        className="w-full xl:w-auto"
      >
        {working ? (
          <Loader2 size={15} className="motion-safe:animate-spin" aria-hidden="true" />
        ) : (
          <Download size={15} aria-hidden="true" />
        )}
        {working ? "Generating PDF…" : "Download PDF report"}
      </Button>

      {status === "error" && (
        <p role="alert" className="text-caption text-danger">
          Unable to generate the report. Please try again.
        </p>
      )}
    </div>
  );
}