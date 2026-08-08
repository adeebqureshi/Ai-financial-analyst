"use client";

import { motion } from "framer-motion";
import {
  CheckCircle2,
  Circle,
  Loader2,
} from "lucide-react";

import { GlassCard } from "@/components/ui/glass-card";

const agents = [
  {
    name: "Planner",
    status: "done",
    description: "Planning analysis",
  },
  {
    name: "Retriever",
    status: "done",
    description: "Reading SEC filings",
  },
  {
    name: "Quant",
    status: "running",
    description: "Running DCF valuation",
  },
  {
    name: "Writer",
    status: "pending",
    description: "Preparing investment report",
  },
  {
    name: "Auditor",
    status: "pending",
    description: "Reviewing output",
  },
] as const;

export function AgentProgress() {
  return (
    <GlassCard className="p-6">
      <h2 className="mb-6 text-xl font-semibold">
        AI Execution
      </h2>

      <div className="space-y-5">
        {agents.map((agent, index) => (
          <motion.div
            key={agent.name}
            initial={{ opacity: 0, x: -15 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.1 }}
            className="flex items-start gap-4"
          >
            {agent.status === "done" && (
              <CheckCircle2
                className="mt-1 text-emerald-400"
                size={20}
              />
            )}

            {agent.status === "running" && (
              <Loader2
                className="mt-1 animate-spin text-blue-400"
                size={20}
              />
            )}

            {agent.status === "pending" && (
              <Circle
                className="mt-1 text-zinc-600"
                size={20}
              />
            )}

            <div>
              <h3 className="font-medium">
                {agent.name}
              </h3>

              <p className="text-sm text-zinc-500">
                {agent.description}
              </p>
            </div>
          </motion.div>
        ))}
      </div>
    </GlassCard>
  );
}