import { notFound } from "next/navigation";

import { AppShell } from "@/components/layout/app-shell";
import { AnalysisView } from "@/components/analysis/analysis-view";
import { api } from "@/services/api";

export const dynamic = "force-dynamic";

type Props = {
  params: Promise<{
    ticker: string;
  }>;
};

export default async function AnalysisTickerPage({
  params,
}: Props) {
  const { ticker } = await params;

  const symbol = ticker.toUpperCase();

  let company;

  try {
    const response = await api.company(symbol);

    if (!response?.data) {
      throw new Error("Company not found");
    }

    company = response.data;
  } catch {
    notFound();
  }

  return (
    <AppShell>
      <div className="mx-auto max-w-7xl">
        <div className="flex flex-col gap-6 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <p className="text-sm uppercase tracking-widest text-zinc-500">
              AI Analysis
            </p>

            <h1 className="mt-3 text-5xl font-bold tracking-tight text-white">
              {company.name}
            </h1>

            <div className="mt-4 flex flex-wrap items-center gap-3">
              <span className="rounded-full border border-blue-500/30 bg-blue-500/10 px-4 py-1.5 text-sm font-semibold text-blue-300">
                {company.ticker}
              </span>

              {company.sector && (
                <span className="rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-sm text-zinc-300">
                  {company.sector}
                </span>
              )}

              {company.industry && (
                <span className="rounded-full border border-white/10 bg-white/5 px-4 py-1.5 text-sm text-zinc-400">
                  {company.industry}
                </span>
              )}
            </div>
          </div>

          <div className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-5 py-3 text-sm font-medium text-emerald-400">
            Backend Connected
          </div>
        </div>

        <AnalysisView ticker={symbol} />
      </div>
    </AppShell>
  );
}
