"use client";

import { Bot } from "lucide-react";

import { ChatSurface } from "@/components/ui/chat-surface";

type AgentWorkspaceProps = {
  caption?: string;
  connection?: React.ReactNode;
};

export function AgentWorkspace({ caption, connection }: AgentWorkspaceProps) {
  return (
    <div className="mx-auto max-w-5xl space-y-10">
      <section className="space-y-6">
        <div className="flex flex-wrap items-center gap-3">
          <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-2 text-sm text-blue-300">
            <Bot size={16} />
            {caption ?? "AI FINANCIAL RESEARCH AGENT"}
          </div>

          {connection}
        </div>

        <h1 className="text-4xl font-bold tracking-tight text-white sm:text-5xl lg:text-6xl">
          Your AI Financial Research Agent
        </h1>

        <p className="max-w-3xl text-lg leading-8 text-zinc-400">
          Analyze companies, read filings, calculate valuation, assess
          risk, and build evidence-backed investment research.
        </p>
      </section>

      <ChatSurface
        placeholder="Compare Nvidia and AMD using their latest annual reports..."
      />
    </div>
  );
}
