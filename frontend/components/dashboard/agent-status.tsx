"use client";

import { motion } from "framer-motion";
import {
  Brain,
  Database,
  Search,
  PenSquare,
  ShieldCheck,
} from "lucide-react";

const agents = [
  {
    name: "Planner",
    status: "Running",
    progress: 100,
    icon: Brain,
  },
  {
    name: "Retriever",
    status: "Ready",
    progress: 95,
    icon: Search,
  },
  {
    name: "Quant",
    status: "Ready",
    progress: 92,
    icon: Database,
  },
  {
    name: "Writer",
    status: "Ready",
    progress: 88,
    icon: PenSquare,
  },
  {
    name: "Auditor",
    status: "Ready",
    progress: 96,
    icon: ShieldCheck,
  },
];

export function AgentStatus() {
  return (
    <div className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl">
      <h2 className="text-2xl font-bold text-white">
        AI Agent Status
      </h2>

      <p className="mt-2 text-zinc-500">
        Real-time orchestration pipeline
      </p>

      <div className="mt-8 space-y-6">
        {agents.map((agent, index) => {
          const Icon = agent.icon;

          return (
            <motion.div
              key={agent.name}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.08 }}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="rounded-2xl bg-blue-500/10 p-3">
                    <Icon
                      size={20}
                      className="text-blue-400"
                    />
                  </div>

                  <div>
                    <div className="font-medium text-white">
                      {agent.name}
                    </div>

                    <div className="text-sm text-zinc-500">
                      {agent.status}
                    </div>
                  </div>
                </div>

                <span className="text-sm text-emerald-400">
                  {agent.progress}%
                </span>
              </div>

              <div className="mt-3 h-2 overflow-hidden rounded-full bg-white/5">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${agent.progress}%` }}
                  transition={{
                    duration: 1,
                    delay: index * 0.1,
                  }}
                  className="h-full rounded-full bg-gradient-to-r from-blue-500 to-cyan-400"
                />
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}