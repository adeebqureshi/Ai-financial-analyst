"use client";

import { useState } from "react";

import { RevenueChart } from "./revenue-chart";
import { IncomeChart } from "./income-chart";
import { BalanceChart } from "./balance-chart";
import { CashFlowChart } from "./cashflow-chart";

type Props = {
  revenue: {
    year: string;
    revenue: number;
  }[];

  income: {
    year: string;
    revenue: number;
    netIncome: number;
  }[];

  balance: {
    year: string;
    assets: number;
    liabilities: number;
  }[];

  cashflow: {
    year: string;
    value: number;
  }[];
};

const tabs = [
  "Revenue",
  "Income",
  "Balance Sheet",
  "Cash Flow",
];

export function ChartTabs({
  revenue,
  income,
  balance,
  cashflow,
}: Props) {
  const [active, setActive] =
    useState("Revenue");

  return (
    <section className="rounded-[36px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl">

      <div className="flex flex-wrap gap-3">

        {tabs.map((tab) => (

          <button
            key={tab}
            onClick={() => setActive(tab)}
            className={`rounded-full px-5 py-2 transition ${
              active === tab
                ? "bg-blue-600 text-white"
                : "bg-white/5 text-zinc-400 hover:bg-white/10"
            }`}
          >
            {tab}
          </button>

        ))}

      </div>

      <div className="mt-8">

        {active === "Revenue" && (
          <RevenueChart revenue={revenue.map(x => x.revenue)} />
        )}

        {active === "Income" && (
          <IncomeChart data={income} />
        )}

        {active === "Balance Sheet" && (
          <BalanceChart data={balance} />
        )}

        {active === "Cash Flow" && (
          <CashFlowChart cashflow={cashflow.map(x => x.value)} />
        )}

      </div>

    </section>
  );
}