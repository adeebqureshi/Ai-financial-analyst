"use client";

import { useCompare } from "@/hooks/use-compare";

const tickers = [
  "AAPL",
  "MSFT",
  "NVDA",
  "GOOGL",
];

const metrics = [
  "Intrinsic Value",
  "Upside",
  "Recommendation",
  "Health Score",
];

function getValue(
  company: {
    ticker: string;
    name: string | null;
    intrinsic_value: number;
    upside: number;
    recommendation: string;
    health_score: number | null;
  },
  metric: string
) {
  switch (metric) {
    case "Intrinsic Value":
      return `$${company.intrinsic_value.toFixed(2)}`;

    case "Upside":
      return `${company.upside.toFixed(2)}%`;

    case "Recommendation":
      return company.recommendation;

    case "Health Score":
      return company.health_score != null
        ? `${company.health_score}/100`
        : "—";

    default:
      return "—";
  }
}

export function ComparisonTable() {
  const { data, isLoading, error } =
    useCompare(tickers);

  if (isLoading) {
    return (
      <div className="rounded-[32px] border border-white/10 bg-white/[0.03] p-12 text-center text-zinc-400">
        Loading comparison...
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-[32px] border border-red-500/20 bg-red-500/5 p-12 text-center text-red-400">
        Failed to load comparison.
      </div>
    );
  }

  const result = data?.data?.results ?? [];

  return (
    <section className="overflow-hidden rounded-[32px] border border-white/10 bg-white/[0.03]">
      <table className="w-full">
        <thead>
          <tr className="border-b border-white/10">
            <th className="p-6 text-left text-zinc-500">
              Metric
            </th>

            {result.map((company) => (
              <th
                key={company.ticker}
                className="p-6 text-center text-white"
              >
                {company.ticker}
              </th>
            ))}
          </tr>
        </thead>

        <tbody>
          {metrics.map((metric) => (
            <tr
              key={metric}
              className="border-b border-white/5 hover:bg-white/[0.02]"
            >
              <td className="p-6 font-medium text-zinc-400">
                {metric}
              </td>

              {result.map((company) => (
                <td
                  key={`${company.ticker}-${metric}`}
                  className="p-6 text-center text-white"
                >
                  {getValue(company, metric)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
