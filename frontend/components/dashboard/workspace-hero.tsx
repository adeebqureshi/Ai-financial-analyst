"use client";

import { motion } from "framer-motion";
import {
  ArrowRight,
  Clock3,
  Search,
  Sparkles,
  TrendingUp,
} from "lucide-react";

import { GlassCard } from "@/components/ui/glass-card";
import { PremiumButton } from "@/components/ui/premium-button";

const recent = [
  "Apple Q3 Earnings",
  "Microsoft DCF",
  "NVIDIA Valuation",
  "Tesla Risk Analysis",
];

const trending = [
  "AAPL DCF",
  "NVDA AI Boom",
  "META Earnings",
  "MSFT Copilot",
];

export function WorkspaceHero() {
  return (
    <section className="mx-auto max-w-6xl">

      <motion.div
        initial={{ opacity: 0, y: 25 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: .6 }}
      >

        <p className="text-zinc-500 text-sm">
          Good Evening,
        </p>

        <h1 className="mt-2 text-6xl font-bold tracking-tight">
          What would you like
          <br />
          to analyze today?
        </h1>

        <p className="mt-6 max-w-3xl text-lg leading-8 text-zinc-400">
          AI-powered equity research,
          institutional valuation,
          SEC analysis,
          portfolio intelligence
          and investment recommendations.
        </p>

      </motion.div>

      <GlassCard
        glow
        className="mt-12 p-5"
      >
        <div className="flex items-center gap-5">

          <Search
            className="text-zinc-500"
            size={22}
          />

          <input
            placeholder="Search Apple, Tesla, NVIDIA..."
            className="
              h-14
              flex-1
              bg-transparent
              text-xl
              outline-none
              placeholder:text-zinc-500
            "
          />

          <PremiumButton size="xl">
            Analyze
          </PremiumButton>

        </div>
      </GlassCard>

      <div className="mt-8 flex flex-wrap gap-3">

        {trending.map((item) => (

          <button
            key={item}
            className="
              rounded-full
              border
              border-white/10
              bg-white/5
              px-5
              py-3
              text-sm
              transition-all
              hover:border-blue-500/30
              hover:bg-blue-500/10
            "
          >
            {item}
          </button>

        ))}

      </div>

      <div className="mt-16 grid gap-6 lg:grid-cols-2">

        <GlassCard className="p-6">

          <div className="mb-5 flex items-center gap-3">

            <Clock3
              className="text-blue-400"
              size={18}
            />

            <h3 className="font-semibold">
              Recent Analysis
            </h3>

          </div>

          <div className="space-y-3">

            {recent.map((item) => (

              <div
                key={item}
                className="
                  flex
                  items-center
                  justify-between
                  rounded-xl
                  bg-white/5
                  px-4
                  py-3
                  transition-all
                  hover:bg-white/10
                "
              >

                <span>{item}</span>

                <ArrowRight size={16} />

              </div>

            ))}

          </div>

        </GlassCard>

        <GlassCard
          glow
          className="p-6"
        >

          <div className="mb-5 flex items-center gap-3">

            <Sparkles
              className="text-blue-400"
              size={18}
            />

            <h3 className="font-semibold">
              AI Insight Today
            </h3>

          </div>

          <div className="space-y-5">

            <div className="flex justify-between">

              <span className="text-zinc-400">
                Market Trend
              </span>

              <span className="flex items-center gap-2 text-emerald-400">

                <TrendingUp size={16} />

                Bullish

              </span>

            </div>

            <div className="rounded-2xl bg-blue-500/10 p-5">

              <p className="leading-8 text-zinc-300">

                Semiconductor stocks
                continue to outperform.

                AI infrastructure
                spending remains
                the strongest catalyst
                across large-cap tech.

              </p>

            </div>

          </div>

        </GlassCard>

      </div>

    </section>
  );
}