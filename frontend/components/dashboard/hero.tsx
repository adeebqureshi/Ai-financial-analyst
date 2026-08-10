"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowRight,
  Sparkles,
  TrendingUp,
} from "lucide-react";

export function DashboardHero() {
  return (
    <motion.section
      initial={{ opacity: 0, y: 25 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 }}
      className="relative overflow-hidden rounded-[32px] border border-white/10 bg-gradient-to-br from-[#0F172A] via-[#090B11] to-[#05060A] p-10"
    >
      <div className="absolute -right-20 -top-20 h-72 w-72 rounded-full bg-blue-500/10 blur-3xl" />
      <div className="absolute -bottom-24 left-10 h-72 w-72 rounded-full bg-violet-500/10 blur-3xl" />

      <div className="relative z-10 flex flex-col justify-between gap-10 xl:flex-row xl:items-center">
        <div className="max-w-3xl">
          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-2 text-sm text-blue-300">
            <Sparkles size={16} />
            AI Insight of the Day
          </div>

          <h1 className="text-6xl font-bold leading-tight tracking-tight text-white">
            Good Morning.
          </h1>

          <p className="mt-6 max-w-2xl text-lg leading-8 text-zinc-400">
            NVIDIA continues showing strong momentum while maintaining
            healthy profitability. Market sentiment remains positive,
            but valuation should be monitored closely.
          </p>

          <Link
            href="/analysis"
            className="mt-8 inline-flex items-center gap-2 rounded-2xl bg-white px-6 py-3 font-medium text-black transition hover:scale-[1.03]"
          >
            Open AI Analysis
            <ArrowRight size={18} />
          </Link>
        </div>

        <div className="grid w-full max-w-md gap-5">
          <div className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
            <div className="text-sm text-zinc-500">
              Market Sentiment
            </div>

            <div className="mt-3 flex items-center gap-3">
              <TrendingUp className="text-emerald-400" />

              <span className="text-4xl font-bold text-white">
                Bullish
              </span>
            </div>

            <p className="mt-4 text-zinc-400">
              Fear &amp; Greed Index:{" "}
              <span className="text-white">74</span>
            </p>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/5 p-6 backdrop-blur-xl">
            <div className="text-sm text-zinc-500">
              Active AI Models
            </div>

            <div className="mt-4 flex gap-2">
              <span className="rounded-full bg-blue-500/20 px-3 py-1 text-sm text-blue-300">
                GPT
              </span>
              <span className="rounded-full bg-violet-500/20 px-3 py-1 text-sm text-violet-300">
                RAG
              </span>
              <span className="rounded-full bg-emerald-500/20 px-3 py-1 text-sm text-emerald-300">
                Finance
              </span>
            </div>
          </div>
        </div>
      </div>
    </motion.section>
  );
}