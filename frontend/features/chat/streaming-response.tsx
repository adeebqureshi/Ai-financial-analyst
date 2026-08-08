"use client";

import { motion } from "framer-motion";

import { GlassCard } from "@/components/ui/glass-card";

export function StreamingResponse() {
  return (
    <GlassCard className="p-8">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <div className="mb-4 flex items-center gap-3">
          <div className="h-3 w-3 rounded-full bg-emerald-400 animate-pulse" />

          <span className="font-semibold">
            AI Financial Analyst
          </span>

          <span className="text-sm text-zinc-500">
            Streaming...
          </span>
        </div>

        <div className="space-y-5 text-[17px] leading-8 text-zinc-300">

          <p>
            Apple continues to demonstrate strong
            operating performance supported by
            consistent revenue growth and expanding
            free cash flow.
          </p>

          <p>
            Discounted Cash Flow analysis suggests
            the stock is trading close to intrinsic
            value with moderate upside under the
            base-case assumptions.
          </p>

          <p>
            Financial quality remains high based on
            Piotroski, Altman Z-Score and operating
            margin stability.
          </p>

        </div>
      </motion.div>
    </GlassCard>
  );
}
