"use client";

import { motion } from "framer-motion";
import {
  ArrowUpRight,
  BarChart3,
  CheckCircle2,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";

import { GlassCard } from "@/components/ui/glass-card";

const metrics = [
  {
    title: "Intrinsic Value",
    value: "$228.34",
  },
  {
    title: "Current Price",
    value: "$214.13",
  },
  {
    title: "Upside",
    value: "+6.63%",
  },
  {
    title: "Confidence",
    value: "92%",
  },
];

export function StreamingResponse() {
  return (
    <GlassCard className="overflow-hidden p-8">

      {/* Header */}

      <div className="flex items-center justify-between">

        <div>

          <div className="flex items-center gap-3">

            <div className="h-3 w-3 rounded-full bg-emerald-400 animate-pulse" />

            <span className="font-semibold text-lg">
              AI Financial Analyst
            </span>

          </div>

          <p className="mt-2 text-sm text-zinc-500">
            Streaming institutional analysis...
          </p>

        </div>

        <div
          className="
            rounded-full
            bg-emerald-500/15
            px-4
            py-2
            text-sm
            font-medium
            text-emerald-400
          "
        >
          BUY
        </div>

      </div>

      {/* Summary */}

      <motion.div
        initial={{
          opacity: 0,
          y: 10,
        }}
        animate={{
          opacity: 1,
          y: 0,
        }}
        transition={{
          delay: .2,
        }}
        className="mt-8"
      >

        <h2 className="text-2xl font-bold">
          Executive Summary
        </h2>

        <p className="mt-5 leading-8 text-zinc-300">

          Apple continues to demonstrate
          exceptional financial strength,
          stable operating margins,
          predictable cash generation
          and industry-leading capital
          allocation.

        </p>

        <p className="mt-5 leading-8 text-zinc-300">

          Our discounted cash flow model
          estimates intrinsic value above
          the current market price,
          suggesting moderate upside
          while maintaining relatively
          low downside risk.

        </p>

      </motion.div>

      {/* Metrics */}

      <div className="mt-10 grid gap-4 md:grid-cols-2 xl:grid-cols-4">

        {metrics.map((metric) => (

          <div
            key={metric.title}
            className="
              rounded-2xl
              border
              border-white/5
              bg-white/[0.04]
              p-5
            "
          >

            <p className="text-sm text-zinc-500">
              {metric.title}
            </p>

            <h3 className="mt-3 text-2xl font-bold">
              {metric.value}
            </h3>

          </div>

        ))}

      </div>

      {/* Investment Thesis */}

      <div className="mt-12">

        <h2 className="text-2xl font-bold">
          Investment Thesis
        </h2>

        <div className="mt-6 space-y-5">

          <div className="flex gap-4">

            <TrendingUp
              className="mt-1 text-blue-400"
              size={20}
            />

            <div>

              <h3 className="font-semibold">
                Revenue Growth
              </h3>

              <p className="mt-2 text-zinc-400 leading-7">
                AI ecosystem expansion
                and premium hardware
                continue driving
                long-term growth.
              </p>

            </div>

          </div>

          <div className="flex gap-4">

            <BarChart3
              className="mt-1 text-purple-400"
              size={20}
            />

            <div>

              <h3 className="font-semibold">
                Strong Cash Flow
              </h3>

              <p className="mt-2 text-zinc-400 leading-7">
                Consistent free cash flow
                supports dividends,
                buybacks
                and innovation.
              </p>

            </div>

          </div>

          <div className="flex gap-4">

            <ShieldCheck
              className="mt-1 text-emerald-400"
              size={20}
            />

            <div>

              <h3 className="font-semibold">
                Risk Assessment
              </h3>

              <p className="mt-2 text-zinc-400 leading-7">
                Financial leverage
                remains conservative
                with excellent
                liquidity metrics.
              </p>

            </div>

          </div>

        </div>

      </div>

      {/* Sources */}

      <div className="mt-12 rounded-2xl border border-white/5 bg-white/[0.03] p-6">

        <h3 className="font-semibold">
          Sources
        </h3>

        <div className="mt-5 space-y-3">

          {[
            "SEC Form 10-K",
            "SEC Form 10-Q",
            "Annual Report",
            "DCF Model",
            "Financial Ratios",
          ].map((item) => (

            <div
              key={item}
              className="flex items-center justify-between"
            >

              <span className="text-zinc-400">
                {item}
              </span>

              <ArrowUpRight
                size={16}
                className="text-zinc-500"
              />

            </div>

          ))}

        </div>

      </div>

      {/* Footer */}

      <div className="mt-10 flex items-center gap-3 text-sm text-emerald-400">

        <CheckCircle2 size={18} />

        Analysis completed successfully.

      </div>

    </GlassCard>
  );
}