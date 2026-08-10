import { AppShell } from "@/components/layout/app-shell";
import { AISearch } from "@/components/dashboard/ai-search";
import { MetricCard } from "@/components/dashboard/metric-card";
import { MarketChart } from "@/components/dashboard/market-chart";
import { AgentStatus } from "@/components/dashboard/agent-status";
import { Watchlist } from "@/components/dashboard/watchlist";
import { NewsFeed } from "@/components/dashboard/news-feed";
import { PortfolioAllocation } from "@/components/dashboard/portfolio-allocation";
import { RecentAnalysis } from "@/components/dashboard/recent-analysis";
import { QuickActions } from "@/components/dashboard/quick-actions";

export default function DashboardPage() {
  return (
    <AppShell>
      <AISearch />

      <section className="mt-10 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="Portfolio Value"
          value="$248,921"
          change={5.4}
          icon="briefcase"
        />

        <MetricCard
          title="Today's Gain"
          value="+$4,312"
          change={2.7}
          icon="trending"
        />

        <MetricCard
          title="Sharpe Ratio"
          value="1.84"
          change={1.8}
          icon="shield"
        />

        <MetricCard
          title="Cash Available"
          value="$42,100"
          change={-1.2}
          icon="dollar"
        />
      </section>

      <section className="mt-10 grid gap-8 xl:grid-cols-[2fr_1fr]">
        <MarketChart />
        <AgentStatus />
      </section>

      <section className="mt-10 grid gap-8 xl:grid-cols-2">
        <Watchlist />
        <NewsFeed />
      </section>

      <section className="mt-10 grid gap-8 xl:grid-cols-2">
        <PortfolioAllocation />
        <RecentAnalysis />
      </section>

      <section className="mt-10">
        <QuickActions />
      </section>
    </AppShell>
  );
}