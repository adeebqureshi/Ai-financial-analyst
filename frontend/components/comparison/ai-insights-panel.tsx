"use client";

import { ArrowUpRight, Sparkles } from "lucide-react";

import { useCopilot } from "@/components/layout/ai-copilot";
import { Button } from "@/components/ui/button";

/**
 * Right-hand insights rail.
 *
 * `/compare` returns computed valuation and health values only — it does not
 * return LLM-generated commentary, so nothing is fabricated here. The panel
 * keeps the reference layout and offers the real AI copilot as the path to
 * generated analysis.
 */
export function AIInsightsPanel() {
  const copilot = useCopilot();

  return (
    <aside
      aria-labelledby="ai-insights-heading"
      className="rounded-2xl border border-border bg-card p-4 shadow-card sm:p-5"
    >
      <div className="flex items-center justify-between gap-3">
        <h2
          id="ai-insights-heading"
          className="flex items-center gap-2 text-[1.0625rem] font-semibold text-foreground"
        >
          <Sparkles size={17} className="text-brand" aria-hidden="true" />
          AI insights
        </h2>

        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={() =>
            copilot.open({ prompt: "Compare these companies on valuation and risk…" })
          }
          className="text-brand hover:text-foreground"
        >
          All insights
          <ArrowUpRight size={14} aria-hidden="true" />
        </Button>
      </div>

      <div className="mt-4 flex flex-col gap-2.5">
        <div className="flex items-start gap-2.5 rounded-xl border border-border bg-surface/50 p-3">
          <span
            className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-lg bg-brand-subtle text-brand"
            aria-hidden="true"
          >
            <Sparkles size={14} />
          </span>
          <p className="text-label leading-relaxed text-foreground">
            AI insights will appear after comparison data is available.
          </p>
        </div>

        <p className="px-1 text-caption leading-relaxed text-muted-foreground">
          The comparison endpoint returns computed valuation and health values
          only. Open the copilot to ask for a written comparison of the selected
          tickers.
        </p>

        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={() =>
            copilot.open({ prompt: "Compare these companies on valuation and risk…" })
          }
          className="mt-1 self-start"
        >
          <Sparkles size={14} className="text-brand" aria-hidden="true" />
          Open AI copilot
        </Button>
      </div>
    </aside>
  );
}
