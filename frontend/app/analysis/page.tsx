import {
  AgentProgress,
  PromptSuggestions,
  StreamingResponse,
  ThinkingTimeline,
} from "@/features/chat";

import { AIInsight } from "@/components/dashboard/ai-insight";
import { AppShell } from "@/components/layout/app-shell";
import { Sidebar } from "@/components/layout/sidebar";

export default function AnalysisPage() {
  return (
    <AppShell
      sidebar={<Sidebar />}
      insights={<AIInsight />}
    >
      <div className="mx-auto max-w-7xl">

        <div className="mb-10">
          <p className="text-sm uppercase tracking-[0.3em] text-blue-400">
            AI Workspace
          </p>

          <h1 className="mt-3 text-5xl font-bold tracking-tight">
            Apple Inc. Analysis
          </h1>

          <p className="mt-4 text-lg text-zinc-400">
            Multi-agent institutional analysis in progress.
          </p>
        </div>

        <div className="grid gap-6 xl:grid-cols-3">

          <div className="space-y-6 xl:col-span-2">
            <StreamingResponse />
            <PromptSuggestions />
          </div>

          <div className="space-y-6">
            <AgentProgress />
            <ThinkingTimeline />
          </div>

        </div>

      </div>
    </AppShell>
  );
}