"use client";

import {
  TrendingUp,
  ShieldCheck,
  Sparkles,
  Target,
} from "lucide-react";

type Props = {
  recommendation: string;
  confidence: number;
  summary: string;
  upside: number;
  intrinsicValue: number;
  currentPrice: number;
};

export function ExecutiveSummary({
  recommendation,
  confidence,
  summary,
  upside,
  intrinsicValue,
  currentPrice,
}: Props) {
  const positive = upside > 0;

  return (
    <section className="rounded-3xl border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl">

      <div className="flex items-center gap-3">
        <Sparkles className="text-blue-400" size={20} />

        <span className="text-sm uppercase tracking-[0.3em] text-zinc-500">
          Executive Summary
        </span>
      </div>

      <div className="mt-8 flex flex-wrap items-center gap-4">

        <div
          className={`rounded-full px-5 py-2 text-lg font-semibold ${
            recommendation === "BUY"
              ? "bg-emerald-500/20 text-emerald-400"
              : recommendation === "SELL"
              ? "bg-red-500/20 text-red-400"
              : "bg-yellow-500/20 text-yellow-300"
          }`}
        >
          {recommendation}
        </div>

        <div className="rounded-full bg-blue-500/20 px-5 py-2 text-blue-300">
          {confidence}% Confidence
        </div>

      </div>

      <p className="mt-8 max-w-4xl text-lg leading-8 text-zinc-300">
        {summary}
      </p>

      <div className="mt-10 grid gap-5 md:grid-cols-4">

        <div className="rounded-2xl bg-white/5 p-5">
          <TrendingUp className="mb-4 text-emerald-400" />
          <div className="text-sm text-zinc-500">
            Upside Potential
          </div>
          <div className="mt-2 text-3xl font-bold text-white">
            {upside.toFixed(2)}%
          </div>
        </div>

        <div className="rounded-2xl bg-white/5 p-5">
          <Target className="mb-4 text-blue-400" />
          <div className="text-sm text-zinc-500">
            Intrinsic Value
          </div>
          <div className="mt-2 text-3xl font-bold text-white">
            ${intrinsicValue.toFixed(2)}
          </div>
        </div>

        <div className="rounded-2xl bg-white/5 p-5">
          <TrendingUp className="mb-4 text-orange-400" />
          <div className="text-sm text-zinc-500">
            Market Price
          </div>
          <div className="mt-2 text-3xl font-bold text-white">
            ${currentPrice.toFixed(2)}
          </div>
        </div>

        <div className="rounded-2xl bg-white/5 p-5">
          <ShieldCheck className="mb-4 text-violet-400" />
          <div className="text-sm text-zinc-500">
            Margin of Safety
          </div>
          <div
            className={`mt-2 text-3xl font-bold ${
              positive ? "text-emerald-400" : "text-red-400"
            }`}
          >
            {(intrinsicValue-currentPrice).toFixed(2)}
          </div>
        </div>

      </div>
    </section>
  );
}