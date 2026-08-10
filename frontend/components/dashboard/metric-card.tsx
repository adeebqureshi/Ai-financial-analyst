"use client";

import { motion } from "framer-motion";
import {
  ArrowDownRight,
  ArrowUpRight,
  Briefcase,
  DollarSign,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";

type MetricCardProps = {
  title: string;
  value: string;
  change: number;
  icon?: "briefcase" | "trending" | "shield" | "dollar";
};

export function MetricCard({
  title,
  value,
  change,
  icon,
}: MetricCardProps) {
  const positive = change >= 0;

  const icons = {
    briefcase: Briefcase,
    trending: TrendingUp,
    shield: ShieldCheck,
    dollar: DollarSign,
  };

  const Icon = icons[icon ?? "trending"];

  return (
    <motion.div
      whileHover={{ y: -6, scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
      className="group relative overflow-hidden rounded-3xl border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 via-transparent to-purple-500/5 opacity-0 transition-opacity duration-300 group-hover:opacity-100" />

      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-sm text-zinc-500">{title}</p>

          <h2 className="mt-3 text-4xl font-bold tracking-tight text-white">
            {value}
          </h2>

          <div
            className={`mt-4 inline-flex items-center gap-1 rounded-full px-3 py-1 text-sm ${
              positive
                ? "bg-emerald-500/10 text-emerald-400"
                : "bg-red-500/10 text-red-400"
            }`}
          >
            {positive ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
            {Math.abs(change)}%
          </div>
        </div>

        <div className="rounded-2xl bg-white/5 p-3">
          <Icon className="text-blue-400" size={24} />
        </div>
      </div>
    </motion.div>
  );
}