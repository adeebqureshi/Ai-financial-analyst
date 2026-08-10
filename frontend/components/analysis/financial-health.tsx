"use client";

import {
  Activity,
  AlertTriangle,
  BarChart3,
  CheckCircle2,
  ShieldCheck,
} from "lucide-react";

type Props = {
  score: number;
  rating: string;
  piotroski: number;
  altman: number;
  beneish: number;
};

function HealthCard({
  title,
  value,
  subtitle,
  color,
  icon,
}: {
  title: string;
  value: string;
  subtitle: string;
  color: string;
  icon: React.ReactNode;
}) {
  return (
    <div className="rounded-[28px] border border-white/10 bg-white/[0.03] p-6 backdrop-blur-xl transition-all duration-300 hover:border-blue-500/30 hover:bg-white/[0.05]">

      <div className={`inline-flex rounded-2xl p-3 ${color}`}>
        {icon}
      </div>

      <p className="mt-5 text-sm text-zinc-500">
        {title}
      </p>

      <h2 className="mt-3 text-4xl font-bold text-white">
        {value}
      </h2>

      <p className="mt-3 text-sm text-zinc-500">
        {subtitle}
      </p>

    </div>
  );
}

export function FinancialHealth({
  score,
  rating,
  piotroski,
  altman,
  beneish,
}: Props) {
  const fraudRisk =
    beneish > -1.78 ? "High" : "Low";

  const bankruptcyRisk =
    altman > 3
      ? "Low"
      : altman > 1.8
      ? "Moderate"
      : "High";

  return (
    <section>

      <div className="mb-8">

        <h2 className="text-3xl font-bold text-white">
          Financial Health
        </h2>

        <p className="mt-2 text-zinc-500">
          AI quality assessment of the business
        </p>

      </div>

      <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-4">

        <HealthCard
          title="Health Score"
          value={`${score}/100`}
          subtitle={rating}
          color="bg-emerald-500/10"
          icon={
            <ShieldCheck
              size={22}
              className="text-emerald-400"
            />
          }
        />

        <HealthCard
          title="Piotroski F Score"
          value={`${piotroski}/9`}
          subtitle="Financial strength"
          color="bg-blue-500/10"
          icon={
            <BarChart3
              size={22}
              className="text-blue-400"
            />
          }
        />

        <HealthCard
          title="Altman Z"
          value={altman.toFixed(2)}
          subtitle={`${bankruptcyRisk} bankruptcy risk`}
          color="bg-violet-500/10"
          icon={
            <CheckCircle2
              size={22}
              className="text-violet-400"
            />
          }
        />

        <HealthCard
          title="Beneish M"
          value={beneish.toFixed(2)}
          subtitle={`${fraudRisk} manipulation risk`}
          color="bg-orange-500/10"
          icon={
            <AlertTriangle
              size={22}
              className="text-orange-400"
            />
          }
        />

      </div>

      <div className="mt-8 rounded-[28px] border border-white/10 bg-gradient-to-r from-emerald-500/5 via-blue-500/5 to-violet-500/5 p-6">

        <div className="flex items-center gap-3">

          <Activity
            size={20}
            className="text-cyan-400"
          />

          <h3 className="text-xl font-semibold text-white">
            AI Financial Interpretation
          </h3>

        </div>

        <div className="mt-6 space-y-3 text-zinc-300 leading-7">

          <p>
            • Financial Health Rating:
            <span className="ml-2 font-semibold text-white">
              {rating}
            </span>
          </p>

          <p>
            • Bankruptcy Risk:
            <span className="ml-2 font-semibold text-white">
              {bankruptcyRisk}
            </span>
          </p>

          <p>
            • Earnings Manipulation Risk:
            <span className="ml-2 font-semibold text-white">
              {fraudRisk}
            </span>
          </p>

          <p>
            • Piotroski analysis indicates
            {" "}
            {piotroski >= 7
              ? "strong financial quality."
              : piotroski >= 5
              ? "average financial quality."
              : "weak financial quality."}
          </p>

        </div>

      </div>

    </section>
  );
}