"use client";

import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";

import { GlassCard } from "@/components/ui/glass-card";

export function AIInsight() {
  return (
    <motion.div
      initial={{
        opacity: 0,
        y: 20,
      }}
      animate={{
        opacity: 1,
        y: 0,
      }}
      transition={{
        delay: 0.15,
      }}
    >
      <GlassCard
        glow
        className="h-full p-6"
      >
        <div className="mb-6 flex items-center gap-3">
          <div className="rounded-xl bg-blue-500/15 p-2 text-blue-400">
            <Sparkles size={18} />
          </div>

          <div>
            <h3 className="font-semibold">
              AI Insight
            </h3>

            <p className="text-xs text-zinc-500">
              Generated just now
            </p>
          </div>
        </div>

        <p className="leading-7 text-zinc-300">
          Technology continues to lead market momentum,
          driven by strong AI infrastructure spending.
          Large-cap semiconductor companies remain
          fundamentally attractive despite premium
          valuations.
        </p>

        <button
          className="
            mt-8
            flex
            items-center
            gap-2
            text-sm
            text-blue-400
            transition-all
            hover:gap-3
          "
        >
          View Full Analysis

          <ArrowRight size={16} />
        </button>
      </GlassCard>
    </motion.div>
  );
}