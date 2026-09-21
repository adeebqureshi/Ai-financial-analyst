import { AISearch } from "@/components/dashboard/ai-search";
import { Watchlist } from "@/components/dashboard/watchlist";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { PageHeader } from "@/components/ui/page-header";

export default function DashboardPage() {
  return (
    <div className="space-y-8">
      <PageHeader
        eyebrow="Financial Workspace"
        title="Your financial data workspace"
        description="Market overview, watchlist, KPIs and portfolio data — supporting tools your AI research agent can invoke."
      />

      <AISearch />

      <section aria-label="Watchlist shortcuts">
        <Watchlist />
      </section>

      <section aria-label="Quick actions">
        <QuickActions />
      </section>
    </div>
  );
}
