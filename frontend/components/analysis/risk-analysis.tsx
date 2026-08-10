"use client";

import {
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  TrendingDown,
} from "lucide-react";

type Props = {
  beta?: number;
  volatility?: number;
  businessRisk?: number;
  financialRisk?: number;
};

function Progress({
  value,
  color,
}: {
  value: number;
  color: string;
}) {
  return (
    <div className="mt-3 h-3 overflow-hidden rounded-full bg-white/10">
      <div
        className={`h-full rounded-full ${color}`}
        style={{
          width: `${Math.max(
            0,
            Math.min(value, 100)
          )}%`,
        }}
      />
    </div>
  );
}

function Card({
  title,
  value,
  unit,
  color,
}: {
  title: string;
  value: number;
  unit?: string;
  color: string;
}) {
  return (
    <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6">

      <p className="text-sm text-zinc-500">
        {title}
      </p>

      <h2 className="mt-3 text-4xl font-bold text-white">
        {value.toFixed(2)}
        {unit}
      </h2>

      <Progress
        value={value}
        color={color}
      />

    </div>
  );
}

export function RiskAnalysis({
  beta = 1.08,
  volatility = 24,
  businessRisk = 32,
  financialRisk = 18,
}: Props) {

  const overall =
    (businessRisk + financialRisk) / 2;

  const overallText =
    overall < 30
      ? "Low Risk"
      : overall < 60
      ? "Moderate Risk"
      : "High Risk";

  return (

    <section>

      <div className="mb-8">

        <h2 className="text-3xl font-bold text-white">
          Risk Analysis
        </h2>

        <p className="mt-2 text-zinc-500">
          AI generated enterprise risk assessment
        </p>

      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">

        <Card
          title="Beta"
          value={beta}
          color="bg-blue-500"
        />

        <Card
          title="Volatility"
          value={volatility}
          unit="%"
          color="bg-orange-500"
        />

        <Card
          title="Business Risk"
          value={businessRisk}
          unit="%"
          color="bg-emerald-500"
        />

        <Card
          title="Financial Risk"
          value={financialRisk}
          unit="%"
          color="bg-red-500"
        />

      </div>

      <div className="mt-8 rounded-[32px] border border-white/10 bg-white/[0.03] p-8">

        <div className="flex items-center justify-between">

          <div>

            <h3 className="text-2xl font-bold text-white">
              Overall AI Risk Score
            </h3>

            <p className="mt-2 text-zinc-500">
              Combined quantitative assessment
            </p>

          </div>

          <div className="text-right">

            <div className="text-5xl font-bold text-white">
              {overall.toFixed(0)}
            </div>

            <div className="mt-2 text-zinc-400">
              /100
            </div>

          </div>

        </div>

        <Progress
          value={overall}
          color="bg-gradient-to-r from-emerald-500 via-yellow-500 to-red-500"
        />

        <div className="mt-8 grid gap-6 md:grid-cols-3">

          <div className="rounded-2xl bg-white/5 p-5">

            <ShieldCheck className="mb-3 text-emerald-400" />

            <h4 className="font-semibold text-white">
              Strengths
            </h4>

            <ul className="mt-4 space-y-2 text-sm text-zinc-400">
              <li>• Strong cash generation</li>
              <li>• Healthy balance sheet</li>
              <li>• Stable earnings</li>
            </ul>

          </div>

          <div className="rounded-2xl bg-white/5 p-5">

            <AlertTriangle className="mb-3 text-yellow-400" />

            <h4 className="font-semibold text-white">
              Watchlist
            </h4>

            <ul className="mt-4 space-y-2 text-sm text-zinc-400">
              <li>• Margin pressure</li>
              <li>• Valuation premium</li>
              <li>• Macro exposure</li>
            </ul>

          </div>

          <div className="rounded-2xl bg-white/5 p-5">

            <ShieldAlert className="mb-3 text-red-400" />

            <h4 className="font-semibold text-white">
              AI Verdict
            </h4>

            <p className="mt-4 text-sm leading-7 text-zinc-400">
              Overall assessment:
              <span className="ml-2 font-semibold text-white">
                {overallText}
              </span>
            </p>

            <div className="mt-5 flex items-center gap-2 text-emerald-400">
              <TrendingDown size={16} />
              Risk remains controlled.
            </div>

          </div>

        </div>

      </div>

    </section>

  );
}