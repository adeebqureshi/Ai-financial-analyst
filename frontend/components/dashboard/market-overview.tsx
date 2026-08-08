"use client";

import { MetricCard } from "./metric-card";

export function MarketOverview() {
  return (
    <section>
      <div className="mb-5 flex items-center justify-between">
        <h2 className="text-2xl font-semibold">
          Market Overview
        </h2>

        <span className="text-sm text-zinc-500">
          Live Overview
        </span>
      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard
          title="S&P 500"
          value="6,438"
          change={1.42}
        />

        <MetricCard
          title="NASDAQ"
          value="21,102"
          change={2.14}
        />

        <MetricCard
          title="Dow Jones"
          value="45,018"
          change={0.64}
        />

        <MetricCard
          title="Fear & Greed"
          value="72"
          change={4.8}
        />
      </div>
    </section>
  );
}