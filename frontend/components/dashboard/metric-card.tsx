"use client";

import { motion } from "framer-motion";
import { TrendingDown, TrendingUp } from "lucide-react";

import { GlassCard } from "@/components/ui/glass-card";
import { cn } from "@/lib/utils";

interface MetricCardProps {
  title: string;
  value: string;
  change: number;
  positive?: boolean;
}

export function MetricCard({
  title,
  value,
  change,
  positive = true,
}: MetricCardProps) {
  return (
    <motion.div
      layout
      whileHover={{
        y: -6,
        scale: 1.02,
      }}
      transition={{
        type: "spring",
        stiffness: 280,
        damping: 20,
      }}
    >
      <GlassCard className="p-6">
        <p className="text-sm text-zinc-400">
          {title}
        </p>

        <h3 className="mt-3 text-3xl font-semibold tracking-tight">
          {value}
        </h3>

        <div
          className={cn(
            "mt-5 flex items-center gap-2 text-sm",
            positive
              ? "text-emerald-400"
              : "text-red-400"
          )}
        >
          {positive ? (
            <TrendingUp size={16} />
          ) : (
            <TrendingDown size={16} />
          )}

          {change}%
        </div>
      </GlassCard>
    </motion.div>
  );
}