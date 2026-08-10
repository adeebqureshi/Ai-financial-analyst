"use client";

import { useState } from "react";
import { FileText, Loader2, Search, Sparkles } from "lucide-react";

import { api } from "@/services/api";
import { ReportViewer } from "@/components/analysis/report-viewer";

import type {
  ApiResponse,
  ReportData,
} from "@/types/analysis";

const suggestions = [
  "AAPL",
  "MSFT",
  "NVDA",
  "TSLA",
  "AMZN",
];

export function ReportWorkspace() {
  const [ticker, setTicker] = useState("");
  const [report, setReport] = useState<ReportData | null>(null);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function generate() {
    const symbol = ticker.trim().toUpperCase();

    if (!/^[A-Z]{1,5}$/.test(symbol) || generating) {
      return;
    }

    setGenerating(true);
    setError(null);
    setReport(null);

    try {
      const response = await api.report({
        ticker: symbol,
      });

      const data = (response as ApiResponse<ReportData>).data;

      if (!data) {
        throw new Error("No report was generated.");
      }

      setReport(data);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to generate the report."
      );
    } finally {
      setGenerating(false);
    }
  }

  return (
    <div className="space-y-10">

      <section className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8">

        <div className="flex h-16 items-center rounded-2xl border border-white/10 bg-white/5 px-6">

          <Search
            size={20}
            className="text-zinc-500"
          />

          <input
            value={ticker}
            onChange={(e) =>
              setTicker(e.target.value)
            }
            onKeyDown={(e) => {
              if (e.key === "Enter") generate();
            }}
            placeholder="Enter ticker (AAPL, MSFT, NVDA...)"
            className="ml-4 flex-1 bg-transparent text-base text-white outline-none placeholder:text-zinc-500"
          />

          <button
            onClick={generate}
            disabled={generating}
            className="flex items-center gap-2 rounded-2xl bg-blue-600 px-6 py-3 font-medium text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {generating ? (
              <>
                <Loader2
                  size={18}
                  className="animate-spin"
                />
                Generating...
              </>
            ) : (
              <>
                <Sparkles size={18} />
                Generate Report
              </>
            )}
          </button>

        </div>

        <div className="mt-6 flex flex-wrap gap-3">

          {suggestions.map((s) => (

            <button
              key={s}
              onClick={() => {
                setTicker(s);
                setReport(null);
              }}
              className="rounded-full border border-white/10 bg-white/5 px-5 py-2 text-sm text-zinc-300 hover:bg-blue-500/10"
            >
              {s}
            </button>

          ))}

        </div>

      </section>

      {error && (
        <section className="rounded-3xl border border-red-500/20 bg-red-500/10 p-8 text-red-300">
          {error}
        </section>
      )}

      {report && (

        <div className="space-y-6">

          <div className="flex items-center gap-3">

            <FileText
              size={22}
              className="text-blue-400"
            />

            <h2 className="text-3xl font-bold text-white">
              {report.title}
            </h2>

          </div>

          <ReportViewer report={report.content} />

        </div>

      )}

    </div>
  );
}
