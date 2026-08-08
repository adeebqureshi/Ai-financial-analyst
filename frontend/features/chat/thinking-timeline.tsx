"use client";

import { motion } from "framer-motion";
import { CheckCircle2, Loader2 } from "lucide-react";

import { GlassCard } from "@/components/ui/glass-card";

const steps = [
  {
    title: "Understanding your request",
    status: "done",
  },
  {
    title: "Searching SEC filings",
    status: "done",
  },
  {
    title: "Computing valuation models",
    status: "running",
  },
  {
    title: "Generating investment thesis",
    status: "pending",
  },
  {
    title: "Confidence verification",
    status: "pending",
  },
] as const;

export function ThinkingTimeline() {
  return (
    <GlassCard className="p-6">
      <h2 className="mb-6 text-xl font-semibold">
        Thinking Process
      </h2>

      <div className="space-y-6">
        {steps.map((step, index) => (
          <motion.div
            key={step.title}
            initial={{ opacity: 0, x: -15 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.08 }}
            className="flex gap-4"
          >
            <div className="mt-1">
              {step.status === "done" && (
                <CheckCircle2
                  className="text-emerald-400"
                  size={18}
                />
              )}

              {step.status === "running" && (
                <Loader2
                  className="animate-spin text-blue-400"
                  size={18}
                />
              )}

              {step.status === "pending" && (
                <div className="h-4 w-4 rounded-full border border-zinc-700" />
              )}
            </div>

            <div>
              <p className="font-medium">
                {step.title}
              </p>

              <p className="mt-1 text-sm text-zinc-500">
                {step.status === "done" && "Completed"}
                {step.status === "running" && "In Progress..."}
                {step.status === "pending" && "Waiting"}
              </p>
            </div>
          </motion.div>
        ))}
      </div>
    </GlassCard>
  );
}