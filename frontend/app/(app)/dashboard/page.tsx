import { AISearch } from "@/components/dashboard/ai-search";
import { StatusStrip } from "@/components/dashboard/status-strip";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { KnowledgeBase } from "@/components/dashboard/knowledge-base";
import { RecentInsights } from "@/components/dashboard/recent-insights";
import { PageHeader } from "@/components/ui/page-header";

/**
 * Command Hub — the application's central launcher.
 *
 * Its job is to answer "what do you want to do?", not to render a financial
 * analysis. Detailed results stay on the Analyze page; this page only starts
 * workflows and surfaces workspace state. Every panel reuses existing hooks
 * and routes, so no additional API traffic is introduced (React Query shares
 * the `health` / `version` / `documents` cache entries).
 */
export default function DashboardPage() {
  return (
    <div className="space-y-10 pb-8">
      <PageHeader
        eyebrow="Financial Workspace"
        title="Command Hub"
        description="Your AI workspace for company analysis, market research, documents and financial intelligence."
      />

      <AISearch />

      <StatusStrip />

      <QuickActions />

      <div className="grid gap-10 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,1fr)] xl:items-start">
        <div className="space-y-10">
          <RecentInsights />
        </div>

        <div className="space-y-10">
          <KnowledgeBase />
        </div>
      </div>
    </div>
  );
}
