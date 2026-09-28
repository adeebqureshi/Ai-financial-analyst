import { AISearch } from "@/components/dashboard/ai-search";
import { StatusStrip } from "@/components/dashboard/status-strip";
import { Watchlist } from "@/components/dashboard/watchlist";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { RecentInsights } from "@/components/dashboard/recent-insights";
import { PageHeader } from "@/components/ui/page-header";

export default function DashboardPage() {
  return (
    <div className="space-y-10 pb-8">
      <PageHeader
        eyebrow="Financial Workspace"
        title="Financial Command Hub"
        description="Research markets, analyze companies, and ask AI — every workflow in this workspace starts here."
      />

      <AISearch />

      <StatusStrip />

      <div className="grid gap-10 xl:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)] xl:items-start">
        <div className="space-y-10">
          <QuickActions />
        </div>

        <div className="space-y-10">
          <RecentInsights />
        </div>
      </div>

      <section aria-label="Watchlist shortcuts">
        <Watchlist />
      </section>
    </div>
  );
}
