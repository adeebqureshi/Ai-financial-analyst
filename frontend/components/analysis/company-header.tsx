"use client";

import {
  Activity,
  Building2,
  Globe,
  Landmark,
} from "lucide-react";

type Props = {
  company: {
    name: string;
    ticker: string;
    sector?: string;
    industry?: string;
    description?: string;
  };

  recommendation: string;

  confidence?: number;
};

function badgeColor(recommendation: string) {
  const r = recommendation.toUpperCase();

  if (r.includes("BUY"))
    return "bg-emerald-500/15 border-emerald-500/30 text-emerald-400";

  if (r.includes("SELL"))
    return "bg-red-500/15 border-red-500/30 text-red-400";

  return "bg-yellow-500/15 border-yellow-500/30 text-yellow-300";
}

export function CompanyHeader({
  company,
  recommendation,
  confidence = 91,
}: Props) {
  return (
    <section className="relative overflow-hidden rounded-[36px] border border-white/10 bg-gradient-to-br from-[#0B1220] via-[#090B11] to-[#05060A] p-10">

      <div className="absolute -right-28 -top-28 h-80 w-80 rounded-full bg-blue-500/10 blur-[120px]" />

      <div className="relative z-10 flex flex-col justify-between gap-10 xl:flex-row">

        <div className="max-w-4xl">

          <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-2 text-sm text-blue-300">
            <Activity size={16} />
            AI Financial Analysis
          </div>

          <h1 className="mt-8 text-6xl font-bold tracking-tight text-white">
            {company.name}
          </h1>

          <div className="mt-6 flex flex-wrap gap-3">

            <span className="rounded-full bg-white/5 px-4 py-2 text-zinc-300">
              {company.ticker}
            </span>

            {company.sector && (
              <span className="rounded-full bg-white/5 px-4 py-2 text-zinc-300">
                <Landmark className="mr-2 inline" size={14} />
                {company.sector}
              </span>
            )}

            {company.industry && (
              <span className="rounded-full bg-white/5 px-4 py-2 text-zinc-300">
                <Building2 className="mr-2 inline" size={14} />
                {company.industry}
              </span>
            )}

          </div>

          <p className="mt-8 max-w-3xl text-lg leading-8 text-zinc-400">
            {company.description ??
              "Enterprise AI generated equity research covering valuation, financial quality, risk assessment, intrinsic value and investment recommendation."}
          </p>

        </div>

        <div className="flex w-full max-w-sm flex-col gap-5">

          <div
            className={`rounded-3xl border p-7 ${badgeColor(
              recommendation
            )}`}
          >
            <div className="text-sm uppercase tracking-[0.25em]">
              Recommendation
            </div>

            <div className="mt-4 text-4xl font-bold">
              {recommendation}
            </div>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/5 p-7">

            <div className="text-sm text-zinc-500">
              AI Confidence
            </div>

            <div className="mt-3 flex items-end gap-2">

              <span className="text-5xl font-bold text-white">
                {confidence}
              </span>

              <span className="pb-2 text-zinc-500">
                %
              </span>

            </div>

            <div className="mt-6 h-2 overflow-hidden rounded-full bg-white/10">

              <div
                className="h-full rounded-full bg-gradient-to-r from-blue-500 via-cyan-400 to-emerald-400"
                style={{
                  width: `${confidence}%`,
                }}
              />

            </div>

          </div>

          <div className="rounded-3xl border border-white/10 bg-white/5 p-6">

            <div className="flex items-center gap-3">

              <Globe
                size={18}
                className="text-blue-400"
              />

              <span className="text-zinc-400">
                Live backend connected
              </span>

            </div>

          </div>

        </div>

      </div>

    </section>
  );
}