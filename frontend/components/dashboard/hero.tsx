"use client";

import { motion } from "framer-motion";
import { Search } from "lucide-react";

import { GlassCard } from "@/components/ui/glass-card";
import { PremiumButton } from "@/components/ui/premium-button";

export function Hero() {
  return (
    <motion.section
      initial={{
        opacity: 0,
        y: 20,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
      transition={{
        duration: 0.6,
      }}
      className="mb-10"
    >
      <GlassCard
        glow
        className="overflow-hidden p-10"
      >
        <div className="max-w-4xl">
          <p className="mb-3 text-sm uppercase tracking-[0.3em] text-blue-400">
            AI Financial Workspace
          </p>

          <h1 className="text-6xl font-bold leading-tight tracking-tight">
            Institutional Research.
            <br />
            Powered by AI.
          </h1>

          <p className="mt-6 max-w-2xl text-lg leading-8 text-zinc-400">
            Analyze companies using live market
            data, SEC filings, valuation
            models and AI reasoning.
          </p>

          <div className="mt-10 flex gap-4">
            <GlassCard className="flex h-14 w-[520px] items-center gap-3 px-5">
              <Search
                className="text-zinc-500"
                size={18}
              />

              <input
                className="flex-1 bg-transparent outline-none placeholder:text-zinc-500"
                placeholder="Search Apple, Microsoft, NVIDIA..."
              />
            </GlassCard>

            <PremiumButton size="xl">
              Analyze
            </PremiumButton>
          </div>
        </div>
      </GlassCard>
    </motion.section>
  );
}