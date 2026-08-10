"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Building2,
  Bot,
  BarChart3,
  FileText,
  ArrowRight,
} from "lucide-react";

const actions = [
  {
    title: "Analyze Company",
    description: "Run complete AI analysis",
    href: "/analysis",
    icon: Building2,
    color: "from-blue-500/20 to-cyan-500/20",
  },
  {
    title: "AI Assistant",
    description: "Ask finance questions",
    href: "/analysis",
    icon: Bot,
    color: "from-violet-500/20 to-fuchsia-500/20",
  },
  {
    title: "Compare Stocks",
    description: "Side-by-side comparison",
    href: "/compare",
    icon: BarChart3,
    color: "from-emerald-500/20 to-teal-500/20",
  },
  {
    title: "Generate Report",
    description: "Export PDF report",
    href: "/reports",
    icon: FileText,
    color: "from-orange-500/20 to-yellow-500/20",
  },
];

export function QuickActions() {
  return (
    <section className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white">
          Quick Actions
        </h2>

        <p className="mt-2 text-zinc-500">
          Launch common workflows
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {actions.map((action, index) => {
          const Icon = action.icon;

          return (
            <Link key={action.title} href={action.href}>
              <motion.button
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.08 }}
                whileHover={{
                  y: -6,
                  scale: 1.02,
                }}
                className={`group w-full rounded-3xl border border-white/10 bg-gradient-to-br ${action.color} p-6 text-left backdrop-blur-xl`}
              >
                <div className="flex items-center justify-between">
                  <div className="rounded-2xl bg-white/10 p-3">
                    <Icon
                      size={24}
                      className="text-white"
                    />
                  </div>

                  <ArrowRight
                    size={18}
                    className="text-zinc-400 transition group-hover:translate-x-1 group-hover:text-white"
                  />
                </div>

                <h3 className="mt-8 text-lg font-semibold text-white">
                  {action.title}
                </h3>

                <p className="mt-2 text-sm text-zinc-300">
                  {action.description}
                </p>
              </motion.button>
            </Link>
          );
        })}
      </div>
    </section>
  );
}
