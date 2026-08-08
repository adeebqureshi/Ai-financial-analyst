"use client";

import {
  Building2,
  Bot,
  Wallet,
  FileText,
} from "lucide-react";

import { GlassCard } from "@/components/ui/glass-card";

const actions = [
  {
    title: "Analyze Company",
    icon: Building2,
  },
  {
    title: "AI Workspace",
    icon: Bot,
  },
  {
    title: "Portfolio",
    icon: Wallet,
  },
  {
    title: "Generate Report",
    icon: FileText,
  },
];

export function QuickActions() {
  return (
    <section className="mt-10">
      <h2 className="mb-5 text-2xl font-semibold">
        Quick Actions
      </h2>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        {actions.map((action) => (
          <GlassCard
            key={action.title}
            className="
              cursor-pointer
              p-6
              transition-all
              hover:border-blue-500/20
            "
          >
            <div className="mb-6 w-fit rounded-2xl bg-blue-500/10 p-3">
              <action.icon
                className="text-blue-400"
                size={22}
              />
            </div>

            <h3 className="font-semibold">
              {action.title}
            </h3>
          </GlassCard>
        ))}
      </div>
    </section>
  );
}