import Link from "next/link";
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
      <section className="mb-10 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm uppercase tracking-widest text-zinc-500">
            Financial Workspace
          </p>

          <h1 className="mt-3 text-4xl font-bold tracking-tight text-white lg:text-5xl">
            Your financial data workspace
          </h1>

          <p className="mt-4 max-w-2xl text-lg text-zinc-400">
            Market overview, watchlist, KPIs and portfolio data — supporting
            tools your AI research agent can invoke.
          </p>
        </div>

        <Link
          href="/"
          className="inline-flex shrink-0 items-center gap-2 rounded-2xl bg-white px-6 py-3 font-medium text-black transition hover:bg-blue-100"
        >
          Ask the AI Agent
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M5 12h14" />
            <path d="m12 5 7 7-7 7" />
          </svg>
        </Link>
      </section>

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
