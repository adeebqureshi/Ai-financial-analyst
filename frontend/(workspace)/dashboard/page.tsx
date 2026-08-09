import AppShell from "@/components/layout/app-shell";
import {
  ArrowDownRight,
  ArrowUpRight,
  Brain,
  ChevronRight,
  CircleDollarSign,
  Globe2,
  Newspaper,
  Search,
  Sparkles,
  TrendingUp,
} from "lucide-react";

const marketData = [
  {
    name: "S&P 500",
    value: "5,842.91",
    change: "+0.84%",
    positive: true,
  },
  {
    name: "NASDAQ",
    value: "18,742.31",
    change: "+1.21%",
    positive: true,
  },
  {
    name: "DOW",
    value: "43,912.10",
    change: "-0.18%",
    positive: false,
  },
  {
    name: "BTC",
    value: "$118,421",
    change: "+2.84%",
    positive: true,
  },
];

const holdings = [
  {
    symbol: "AAPL",
    name: "Apple Inc.",
    value: "$18,420",
    change: "+4.82%",
  },
  {
    symbol: "NVDA",
    name: "NVIDIA Corp.",
    value: "$14,850",
    change: "+8.31%",
  },
  {
    symbol: "MSFT",
    name: "Microsoft Corp.",
    value: "$12,620",
    change: "+2.14%",
  },
  {
    symbol: "AMZN",
    name: "Amazon.com",
    value: "$8,940",
    change: "-0.62%",
  },
];

const newsItems = [
  {
    category: "MARKETS",
    title:
      "Technology stocks lead the market higher as earnings expectations rise",
  },
  {
    category: "MACRO",
    title:
      "Federal Reserve signals continued data-dependent approach",
  },
  {
    category: "AI",
    title:
      "AI infrastructure spending remains strong across major cloud providers",
  },
];

export default function DashboardPage() {
  return (
    <AppShell>
      <main className="min-h-screen bg-[#050608] text-white">
        {/* Background glow */}
        <div className="pointer-events-none fixed inset-0 -z-0 overflow-hidden">
          <div className="absolute left-[15%] top-[-15%] h-[420px] w-[420px] rounded-full bg-blue-500/10 blur-[140px]" />

          <div className="absolute right-[-5%] top-[20%] h-[360px] w-[360px] rounded-full bg-violet-500/10 blur-[140px]" />
        </div>

        <div className="relative z-10 mx-auto max-w-[1600px] px-5 py-7 sm:px-6 lg:px-10">
          {/* Header */}
          <header className="mb-8 flex items-start justify-between gap-6">
            <div>
              <div className="mb-2 flex items-center gap-2 text-sm text-zinc-500">
                <span>Workspace</span>

                <ChevronRight size={14} />

                <span className="text-zinc-300">Dashboard</span>
              </div>

              <h1 className="text-3xl font-semibold tracking-tight sm:text-4xl">
                Good morning, Adeeb.
              </h1>

              <p className="mt-2 text-sm text-zinc-500">
                Here&apos;s what&apos;s happening across your portfolio and the
                markets.
              </p>
            </div>

            {/* Search */}
            <button
              type="button"
              className="hidden items-center gap-2 rounded-xl border border-white/10 bg-white/[0.04] px-4 py-2.5 text-sm text-zinc-300 transition hover:bg-white/[0.08] md:flex"
            >
              <Search size={16} />

              <span>Search anything</span>

              <kbd className="rounded-md border border-white/10 px-1.5 py-0.5 text-[10px] text-zinc-500">
                ⌘ K
              </kbd>
            </button>
          </header>

          {/* KPI cards */}
          <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard
              label="Portfolio Value"
              value="$84,730.42"
              change="+12.84%"
              icon={<CircleDollarSign size={19} />}
              positive
            />

            <MetricCard
              label="Today's P&L"
              value="+$1,284.31"
              change="+1.54%"
              icon={<TrendingUp size={19} />}
              positive
            />

            <MetricCard
              label="AI Confidence"
              value="92.4%"
              change="+4.2%"
              icon={<Brain size={19} />}
              positive
            />

            <MetricCard
              label="Market Sentiment"
              value="Bullish"
              change="Strong"
              icon={<Globe2 size={19} />}
              positive
            />
          </section>

          {/* Main dashboard */}
          <section className="mt-5 grid gap-5 xl:grid-cols-[minmax(0,1fr)_390px]">
            {/* Portfolio performance */}
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.025] p-5 backdrop-blur-xl sm:p-6">
              <div className="mb-6 flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm text-zinc-500">
                    Portfolio performance
                  </p>

                  <div className="mt-1 flex items-end gap-3">
                    <h2 className="text-3xl font-semibold tracking-tight">
                      $84,730.42
                    </h2>

                    <span className="mb-1 flex items-center gap-1 text-sm text-emerald-400">
                      <ArrowUpRight size={15} />
                      12.84%
                    </span>
                  </div>
                </div>

                {/* Period selector */}
                <div className="flex shrink-0 rounded-lg border border-white/[0.08] bg-white/[0.03] p-1">
                  {["1D", "1W", "1M", "1Y"].map((period, index) => (
                    <button
                      key={period}
                      type="button"
                      className={`rounded-md px-3 py-1.5 text-xs transition ${
                        index === 2
                          ? "bg-white/10 text-white"
                          : "text-zinc-500 hover:text-white"
                      }`}
                    >
                      {period}
                    </button>
                  ))}
                </div>
              </div>

              {/* Chart */}
              <div className="relative h-[300px] overflow-hidden rounded-xl">
                {/* Grid */}
                <div className="absolute inset-0 flex flex-col justify-between">
                  {[0, 1, 2, 3, 4].map((line) => (
                    <div
                      key={line}
                      className="border-t border-white/[0.045]"
                    />
                  ))}
                </div>

                <svg
                  className="absolute inset-0 h-full w-full"
                  viewBox="0 0 1000 300"
                  preserveAspectRatio="none"
                  aria-label="Portfolio performance chart"
                  role="img"
                >
                  <defs>
                    <linearGradient
                      id="portfolioGradient"
                      x1="0"
                      y1="0"
                      x2="0"
                      y2="1"
                    >
                      <stop
                        offset="0%"
                        stopColor="#60a5fa"
                        stopOpacity="0.28"
                      />

                      <stop
                        offset="100%"
                        stopColor="#60a5fa"
                        stopOpacity="0"
                      />
                    </linearGradient>
                  </defs>

                  <path
                    d="M0 240
                    C80 225 100 250 170 215
                    C230 185 250 210 310 180
                    C370 150 410 185 470 150
                    C530 115 570 145 620 125
                    C690 95 710 125 770 85
                    C830 48 880 78 930 45
                    C960 28 980 34 1000 20
                    L1000 300
                    L0 300
                    Z"
                    fill="url(#portfolioGradient)"
                  />

                  <path
                    d="M0 240
                    C80 225 100 250 170 215
                    C230 185 250 210 310 180
                    C370 150 410 185 470 150
                    C530 115 570 145 620 125
                    C690 95 710 125 770 85
                    C830 48 880 78 930 45
                    C960 28 980 34 1000 20"
                    fill="none"
                    stroke="#60a5fa"
                    strokeWidth="3"
                    vectorEffect="non-scaling-stroke"
                  />
                </svg>

                {/* Chart labels */}
                <div className="absolute bottom-2 left-0 right-0 flex justify-between text-[11px] text-zinc-600">
                  <span>Jul 10</span>
                  <span>Jul 17</span>
                  <span>Jul 24</span>
                  <span>Jul 31</span>
                  <span>Aug 07</span>
                </div>
              </div>
            </div>

            {/* AI Insight */}
            <div className="relative overflow-hidden rounded-2xl border border-blue-400/10 bg-gradient-to-br from-blue-500/[0.09] to-violet-500/[0.04] p-6">
              <div className="absolute right-[-40px] top-[-40px] h-40 w-40 rounded-full bg-blue-500/10 blur-3xl" />

              <div className="relative">
                <div className="mb-5 flex items-center justify-between gap-3">
                  <div className="flex items-center gap-2">
                    <div className="rounded-lg border border-blue-400/20 bg-blue-400/10 p-2">
                      <Sparkles
                        size={17}
                        className="text-blue-300"
                      />
                    </div>

                    <div>
                      <p className="text-sm font-medium">
                        AI Analyst
                      </p>

                      <p className="text-[11px] text-zinc-500">
                        Updated 2 min ago
                      </p>
                    </div>
                  </div>

                  <span className="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2.5 py-1 text-[10px] text-emerald-400">
                    92% confidence
                  </span>
                </div>

                <h3 className="text-xl font-medium leading-snug">
                  Your portfolio is positioned well for the current
                  market.
                </h3>

                <p className="mt-4 text-sm leading-6 text-zinc-400">
                  NVIDIA and Apple are driving most of your recent
                  gains. However, your technology exposure has increased
                  to 61%.
                </p>

                <div className="mt-5 rounded-xl border border-white/[0.07] bg-black/20 p-4">
                  <p className="text-xs uppercase tracking-wider text-zinc-600">
                    AI recommendation
                  </p>

                  <p className="mt-2 text-sm leading-6 text-zinc-300">
                    Consider reducing concentration risk by allocating
                    5–8% to defensive sectors.
                  </p>
                </div>

                <button
                  type="button"
                  className="mt-5 flex w-full items-center justify-center gap-2 rounded-xl bg-white px-4 py-3 text-sm font-medium text-black transition hover:bg-zinc-200"
                >
                  View full analysis
                  <ArrowUpRight size={15} />
                </button>
              </div>
            </div>
          </section>

          {/* Holdings + Markets */}
          <section className="mt-5 grid gap-5 lg:grid-cols-2">
            {/* Holdings */}
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.025] p-5 sm:p-6">
              <div className="mb-5 flex items-center justify-between gap-4">
                <div>
                  <h2 className="font-medium">Top holdings</h2>

                  <p className="mt-1 text-xs text-zinc-500">
                    Your largest portfolio positions
                  </p>
                </div>

                <button
                  type="button"
                  className="text-xs text-blue-400 transition hover:text-blue-300"
                >
                  View portfolio
                </button>
              </div>

              <div className="space-y-2">
                {holdings.map((holding) => (
                  <div
                    key={holding.symbol}
                    className="flex items-center justify-between rounded-xl border border-transparent p-3 transition hover:border-white/[0.06] hover:bg-white/[0.025]"
                  >
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.06] text-xs font-semibold">
                        {holding.symbol.slice(0, 2)}
                      </div>

                      <div>
                        <p className="text-sm font-medium">
                          {holding.symbol}
                        </p>

                        <p className="text-xs text-zinc-500">
                          {holding.name}
                        </p>
                      </div>
                    </div>

                    <div className="text-right">
                      <p className="text-sm font-medium">
                        {holding.value}
                      </p>

                      <p
                        className={`text-xs ${
                          holding.change.startsWith("+")
                            ? "text-emerald-400"
                            : "text-red-400"
                        }`}
                      >
                        {holding.change}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Markets */}
            <div className="rounded-2xl border border-white/[0.08] bg-white/[0.025] p-5 sm:p-6">
              <div className="mb-5 flex items-center justify-between">
                <div>
                  <h2 className="font-medium">Markets</h2>

                  <p className="mt-1 text-xs text-zinc-500">
                    Global market snapshot
                  </p>
                </div>

                <div className="flex items-center gap-2 text-xs text-emerald-400">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
                  Live
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                {marketData.map((market) => (
                  <div
                    key={market.name}
                    className="rounded-xl border border-white/[0.06] bg-black/20 p-4"
                  >
                    <p className="text-xs text-zinc-500">
                      {market.name}
                    </p>

                    <p className="mt-2 text-lg font-medium">
                      {market.value}
                    </p>

                    <div
                      className={`mt-1 flex items-center gap-1 text-xs ${
                        market.positive
                          ? "text-emerald-400"
                          : "text-red-400"
                      }`}
                    >
                      {market.positive ? (
                        <ArrowUpRight size={13} />
                      ) : (
                        <ArrowDownRight size={13} />
                      )}

                      {market.change}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          {/* Market intelligence */}
          <section className="mt-5 rounded-2xl border border-white/[0.08] bg-white/[0.025] p-5 sm:p-6">
            <div className="mb-5 flex items-center gap-2">
              <Newspaper
                size={17}
                className="text-zinc-400"
              />

              <h2 className="font-medium">
                Market intelligence
              </h2>
            </div>

            <div className="grid gap-3 md:grid-cols-3">
              {newsItems.map((item) => (
                <article
                  key={item.title}
                  className="group cursor-pointer rounded-xl border border-white/[0.06] p-4 transition hover:border-white/[0.12] hover:bg-white/[0.03]"
                >
                  <p className="text-[11px] text-zinc-600">
                    {item.category}
                  </p>

                  <h3 className="mt-2 text-sm leading-5 text-zinc-300 transition group-hover:text-white">
                    {item.title}
                  </h3>

                  <p className="mt-3 text-[11px] text-zinc-600">
                    12 minutes ago
                  </p>
                </article>
              ))}
            </div>
          </section>
        </div>
      </main>
    </AppShell>
  );
}

function MetricCard({
  label,
  value,
  change,
  icon,
  positive,
}: {
  label: string;
  value: string;
  change: string;
  icon: React.ReactNode;
  positive: boolean;
}) {
  return (
    <div className="group rounded-2xl border border-white/[0.08] bg-white/[0.025] p-5 transition duration-300 hover:-translate-y-0.5 hover:border-white/[0.14] hover:bg-white/[0.04]">
      <div className="flex items-center justify-between">
        <span className="text-sm text-zinc-500">
          {label}
        </span>

        <div className="rounded-lg border border-white/[0.06] bg-white/[0.04] p-2 text-zinc-400 transition group-hover:text-white">
          {icon}
        </div>
      </div>

      <div className="mt-5 flex items-end justify-between gap-3">
        <p className="text-2xl font-semibold tracking-tight">
          {value}
        </p>

        <span
          className={`text-xs ${
            positive
              ? "text-emerald-400"
              : "text-red-400"
          }`}
        >
          {change}
        </span>
      </div>
    </div>
  );
}