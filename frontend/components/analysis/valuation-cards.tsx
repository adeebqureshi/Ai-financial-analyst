"use client";

import {
  Activity,
  BadgeDollarSign,
  Calculator,
  DollarSign,
  TrendingDown,
  TrendingUp,
} from "lucide-react";

type Props = {
  intrinsicValue: number;
  currentPrice: number;
  upside: number;
  discountRate: number;
};

function currency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

function Card({
  title,
  value,
  subtitle,
  icon,
  accent,
}: {
  title: string;
  value: string;
  subtitle: string;
  icon: React.ReactNode;
  accent: string;
}) {
  return (
    <div className="group rounded-[28px] border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl transition-all duration-300 hover:-translate-y-1 hover:border-blue-500/30 hover:bg-white/[0.05]">

      <div
        className={`inline-flex rounded-2xl p-3 ${accent}`}
      >
        {icon}
      </div>

      <p className="mt-5 text-sm text-zinc-500">
        {title}
      </p>

      <h2 className="mt-3 text-4xl font-bold tracking-tight text-white">
        {value}
      </h2>

      <p className="mt-3 text-sm text-zinc-500">
        {subtitle}
      </p>

    </div>
  );
}

export function ValuationCards({
  intrinsicValue,
  currentPrice,
  upside,
  discountRate,
}: Props) {

  const margin =
    intrinsicValue - currentPrice;

  return (

    <section>

      <div className="mb-8">

        <h2 className="text-3xl font-bold text-white">
          Valuation
        </h2>

        <p className="mt-2 text-zinc-500">
          AI generated intrinsic value model
        </p>

      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">

        <Card
          title="Intrinsic Value"
          value={currency(intrinsicValue)}
          subtitle="Estimated fair value"
          icon={
            <BadgeDollarSign
              className="text-blue-400"
              size={22}
            />
          }
          accent="bg-blue-500/10"
        />

        <Card
          title="Current Price"
          value={currency(currentPrice)}
          subtitle="Latest market price"
          icon={
            <DollarSign
              className="text-emerald-400"
              size={22}
            />
          }
          accent="bg-emerald-500/10"
        />

        <Card
          title="Upside"
          value={`${upside.toFixed(2)}%`}
          subtitle={
            upside >= 0
              ? "Potential appreciation"
              : "Potential downside"
          }
          icon={
            upside >= 0 ? (
              <TrendingUp
                className="text-green-400"
                size={22}
              />
            ) : (
              <TrendingDown
                className="text-red-400"
                size={22}
              />
            )
          }
          accent={
            upside >= 0
              ? "bg-green-500/10"
              : "bg-red-500/10"
          }
        />

        <Card
          title="Discount Rate"
          value={`${(
            discountRate * 100
          ).toFixed(2)}%`}
          subtitle={`Margin of Safety ${currency(
            margin
          )}`}
          icon={
            <Calculator
              className="text-violet-400"
              size={22}
            />
          }
          accent="bg-violet-500/10"
        />

      </div>

      <div className="mt-8 rounded-[28px] border border-white/10 bg-gradient-to-r from-blue-500/5 via-cyan-500/5 to-emerald-500/5 p-6">

        <div className="flex items-center gap-3">

          <Activity
            size={20}
            className="text-cyan-400"
          />

          <h3 className="text-xl font-semibold text-white">
            AI Valuation Insight
          </h3>

        </div>

        <p className="mt-4 leading-8 text-zinc-300">
          {upside >= 15
            ? "The model estimates that the company is trading below its intrinsic value, indicating a potentially attractive long-term opportunity."
            : upside <= -15
            ? "The model estimates that the company is trading above intrinsic value, suggesting limited upside under current assumptions."
            : "The current market price is close to estimated intrinsic value, suggesting a fairly valued business under current assumptions."}
        </p>

      </div>

    </section>

  );
}