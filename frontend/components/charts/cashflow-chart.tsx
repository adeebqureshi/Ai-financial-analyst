"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Props = {
  cashflow: number[];
};

export function CashFlowChart({
  cashflow,
}: Props) {

  const data = cashflow.map((v, i) => ({
    year: `FY${2020 + i}`,
    value: v,
  }));

  return (

    <section className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8">

      <div className="mb-8">

        <h2 className="text-2xl font-bold text-white">
          Free Cash Flow
        </h2>

      </div>

      <div className="h-[420px]">

        <ResponsiveContainer>

          <BarChart data={data}>

            <CartesianGrid
              stroke="#222"
              vertical={false}
            />

            <XAxis
              dataKey="year"
              stroke="#666"
            />

            <YAxis stroke="#666" />

            <Tooltip
              contentStyle={{
                background:"#111827",
                borderRadius:16,
              }}
            />

            <Bar
              dataKey="value"
              radius={[10,10,0,0]}
              fill="#10b981"
            />

          </BarChart>

        </ResponsiveContainer>

      </div>

    </section>

  );

}