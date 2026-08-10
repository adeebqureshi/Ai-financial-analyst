"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ArrowRight, Search, Sparkles } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";

export default function AnalysisPage() {
  const router = useRouter();
  const [ticker, setTicker] = useState("");

  function submit() {
    const symbol = ticker.trim().toUpperCase();

    if (!/^[A-Z]{1,5}$/.test(symbol)) return;

    router.push(`/analysis/${symbol}`);
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl">
        <div className="mb-12">
          <p className="text-sm uppercase tracking-widest text-blue-400">
            Analysis Tool
          </p>

          <h1 className="mt-3 text-5xl font-bold tracking-tight text-white">
            Company Analysis
          </h1>

          <p className="mt-4 text-lg text-zinc-400">
            Run a comprehensive AI-driven financial analysis for any public
            company — valuation, financial health, risk and recommendation.
          </p>

          <p className="mt-3 text-sm text-zinc-500">
            You can also ask the{" "}
            <Link
              href="/"
              className="text-blue-400 underline underline-offset-2 hover:text-blue-300"
            >
              AI financial agent
            </Link>{" "}
            to run this analysis from a natural-language question.
          </p>
        </div>

        <section className="rounded-[32px] border border-white/10 bg-white/[0.03] p-10">
          <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-2 text-sm text-blue-300">
            <Sparkles size={16} />
            Ticker
          </div>

          <div className="mt-8 flex h-20 items-center rounded-3xl border border-white/10 bg-white/5 px-6">
            <Search
              size={24}
              className="text-zinc-500"
            />

            <input
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") submit();
              }}
              placeholder="Enter ticker (AAPL, MSFT, NVDA...)"
              className="ml-5 flex-1 bg-transparent text-lg text-white outline-none"
            />

            <button
              onClick={submit}
              disabled={!/^[A-Z]{1,5}$/i.test(ticker)}
              className="flex items-center gap-2 rounded-2xl bg-white px-6 py-3 font-medium text-black disabled:cursor-not-allowed disabled:opacity-40"
            >
              Analyze
              <ArrowRight size={18} />
            </button>
          </div>

          <p className="mt-6 text-sm text-zinc-500">
            Enter a ticker symbol (1-5 letters) to begin the analysis.
          </p>
        </section>
      </div>
    </AppShell>
  );
}
