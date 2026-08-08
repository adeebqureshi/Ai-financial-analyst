import {
  AgentProgress,
  ChatInput,
  CompanyHeader,
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
      <div className="mx-auto max-w-7xl space-y-8">

        {/* Company Header */}

        <CompanyHeader />

        {/* Workspace */}

        <div className="grid gap-6 xl:grid-cols-3">

          {/* Main Content */}

          <div className="space-y-6 xl:col-span-2">

            <ChatInput />

            <StreamingResponse />

            <PromptSuggestions />

          </div>

          {/* Right Sidebar */}

          <div className="space-y-6">

            <AgentProgress />

            <ThinkingTimeline />

          </div>

        </div>

      </div>
    </AppShell>
  );
}