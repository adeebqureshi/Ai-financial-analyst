"use client";

import Link from "next/link";
import {
  ArrowUpRight,
  ArrowRight,
} from "lucide-react";

const analyses = [
  {
    company: "Apple",
    ticker: "AAPL",
    recommendation: "BUY",
    confidence: 95,
    date: "Today",
  },
  {
    company: "Microsoft",
    ticker: "MSFT",
    recommendation: "BUY",
    confidence: 91,
    date: "Today",
  },
  {
    company: "NVIDIA",
    ticker: "NVDA",
    recommendation: "HOLD",
    confidence: 86,
    date: "Yesterday",
  },
  {
    company: "Tesla",
    ticker: "TSLA",
    recommendation: "SELL",
    confidence: 72,
    date: "Yesterday",
  },
];

export function RecentAnalysis() {
  return (
    <section className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl">

      <div className="mb-8 flex items-center justify-between">

        <div>

          <h2 className="text-2xl font-bold text-white">
            Recent AI Analyses
          </h2>

          <p className="mt-2 text-zinc-500">
            Latest generated investment reports
          </p>

        </div>

        <button className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-sm text-zinc-300 transition hover:bg-white/10">
          View All
        </button>

      </div>

      <div className="space-y-4">

        {analyses.map((item) => (

            <Link

              key={item.ticker}

              href={`/analysis/${item.ticker}`}

              className="flex items-center justify-between rounded-2xl border border-white/5 bg-white/[0.02] px-6 py-5 transition hover:border-blue-500/20 hover:bg-blue-500/5"

            >

              <div>

                <h3 className="font-semibold text-white">
                  {item.company}
                </h3>

                <p className="mt-1 text-sm text-zinc-500">
                  {item.ticker}
                </p>

              </div>

              <div>

                <span
                  className={`rounded-full px-3 py-1 text-xs font-semibold ${
                    item.recommendation === "BUY"
                      ? "bg-emerald-500/10 text-emerald-400"
                      : item.recommendation === "SELL"
                      ? "bg-red-500/10 text-red-400"
                      : "bg-yellow-500/10 text-yellow-400"
                  }`}
                >
                  {item.recommendation}
                </span>

              </div>

              <div className="text-center">

                <div className="text-lg font-bold text-white">
                  {item.confidence}%
                </div>

                <div className="text-xs text-zinc-500">
                  Confidence
                </div>

              </div>

              <div className="text-zinc-500">

                {item.date}

              </div>

              <button className="rounded-xl border border-white/10 bg-white/5 p-3 transition hover:bg-blue-500/10">

                <ArrowRight
                  size={18}
                  className="text-blue-400"
                />

              </button>

            </Link>

        ))}

      </div>

      <div className="mt-8 flex items-center gap-2 text-sm text-blue-400">

        <ArrowUpRight size={16} />

        24 analyses generated this week

      </div>

    </section>
  );
}