"use client";

import { motion } from "framer-motion";
import {
  ArrowRight,
  Search,
  Sparkles,
} from "lucide-react";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAnalysis } from "@/hooks/use-analysis";

const suggestions = [
  "AAPL",
  "MSFT",
  "NVDA",
  "TSLA",
  "AMZN",
  "GOOGL",
];

export function AISearch() {
  const router = useRouter();

  const [ticker, setTicker] = useState("");

  const analysis = useAnalysis();

  async function submit() {
    if (!ticker.trim()) return;

    try {
      await analysis.mutateAsync(
        ticker.toUpperCase()
      );

      router.push(
        `/analysis/${ticker.toUpperCase()}`
      );
    } catch (err) {
      console.error("FULL ERROR:", err);

      if (err instanceof Error) {
        alert(err.message);
      } else {
        alert(JSON.stringify(err));
      }
    }
  }

  return (
    <motion.section
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="relative overflow-hidden rounded-[32px] border border-white/10 bg-gradient-to-br from-[#0B1220] via-[#090B11] to-[#05060A] p-10"
    >
      <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-2 text-sm text-blue-300">
        <Sparkles size={16} />
        AI Workspace
      </div>

      <h1 className="mt-8 text-6xl font-bold leading-tight text-white">
        Ask AI about
        <br />
        any public company.
      </h1>

      <p className="mt-6 max-w-3xl text-lg text-zinc-400">
        AI powered investment research,
        valuation, financial ratios,
        intrinsic value and risk analysis.
      </p>

      <div className="mt-10 flex h-20 items-center rounded-3xl border border-white/10 bg-white/5 px-6">

        <Search
          size={24}
          className="text-zinc-500"
        />

        <input
          value={ticker}
          onChange={(e) =>
            setTicker(e.target.value)
          }
          onKeyDown={(e) => {
            if (e.key === "Enter")
              submit();
          }}
          placeholder="Enter ticker (AAPL, MSFT, NVDA...)"
          className="ml-5 flex-1 bg-transparent text-lg text-white outline-none"
        />

        <button
          disabled={analysis.isPending}
          onClick={submit}
          className="rounded-2xl bg-white px-6 py-3 font-medium text-black"
        >
          {analysis.isPending
            ? "Analyzing..."
            : (
              <>
                Analyze
                <ArrowRight
                  className="ml-2 inline"
                  size={18}
                />
              </>
            )}
        </button>

      </div>

      <div className="mt-8 flex flex-wrap gap-3">

        {suggestions.map((s) => (

          <button
            key={s}
            onClick={() => setTicker(s)}
            className="rounded-full border border-white/10 bg-white/5 px-5 py-2 text-sm text-zinc-300 hover:bg-blue-500/10"
          >
            {s}
          </button>

        ))}

      </div>

    </motion.section>
  );
}