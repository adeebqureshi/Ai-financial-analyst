import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowRight, Building2 } from "lucide-react";

import { AppShell } from "@/components/layout/app-shell";
import { api } from "@/services/api";

export const dynamic = "force-dynamic";

export default async function CompanyDetailPage({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
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
          <div className="flex items-center gap-6">
            <div className="flex h-20 w-20 items-center justify-center rounded-3xl bg-gradient-to-br from-blue-500/20 to-indigo-500/20">
              <Building2 size={36} className="text-blue-400" />
            </div>

            <div>
              <h1 className="text-4xl font-bold tracking-tight text-white">
                {company.name}
              </h1>

              <div className="mt-3 flex flex-wrap items-center gap-3">
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
          </div>

          <Link
            href={`/analysis/${company.ticker}`}
            className="inline-flex items-center gap-2 rounded-2xl bg-white px-6 py-3 font-medium text-black transition hover:scale-[1.02]"
          >
            Run AI Analysis
            <ArrowRight size={18} />
          </Link>
        </div>

        <section className="mt-10 rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl">
          <h2 className="text-2xl font-bold text-white">
            Company Profile
          </h2>

          <div className="mt-8 grid gap-6 md:grid-cols-2 xl:grid-cols-4">
            <div className="rounded-2xl border border-white/5 bg-white/[0.04] p-5">
              <p className="text-sm text-zinc-500">Ticker</p>
              <h3 className="mt-2 text-2xl font-bold text-white">
                {company.ticker}
              </h3>
            </div>

            <div className="rounded-2xl border border-white/5 bg-white/[0.04] p-5">
              <p className="text-sm text-zinc-500">Sector</p>
              <h3 className="mt-2 text-2xl font-bold text-white">
                {company.sector ?? "N/A"}
              </h3>
            </div>

            <div className="rounded-2xl border border-white/5 bg-white/[0.04] p-5">
              <p className="text-sm text-zinc-500">Industry</p>
              <h3 className="mt-2 text-2xl font-bold text-white">
                {company.industry ?? "N/A"}
              </h3>
            </div>

            <div className="rounded-2xl border border-white/5 bg-white/[0.04] p-5">
              <p className="text-sm text-zinc-500">Market Cap</p>
              <h3 className="mt-2 text-2xl font-bold text-white">
                {company.market_cap
                  ? `$${(company.market_cap / 1_000_000_000).toFixed(2)}B`
                  : "N/A"}
              </h3>
            </div>
          </div>

          {company.description && (
            <p className="mt-8 max-w-4xl leading-8 text-zinc-300">
              {company.description}
            </p>
          )}
        </section>
      </div>
    </AppShell>
  );
}
