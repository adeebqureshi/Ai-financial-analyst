"use client";

import {
  Bar,
  BarChart,
  ResponsiveContainer,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Props = {
  data: {
    year: string;
    assets: number;
    liabilities: number;
  }[];
};

export function BalanceChart({ data }: Props) {
  return (

    <section className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8">

      <div className="mb-8">

        <h2 className="text-2xl font-bold text-white">
          Assets vs Liabilities
        </h2>

      </div>

      <div className="h-[420px]">

        <ResponsiveContainer>

          <BarChart data={data}>

            <CartesianGrid
              stroke="#27272a"
              vertical={false}
            />

            <XAxis
              dataKey="year"
              stroke="#71717a"
            />

            <YAxis stroke="#71717a" />

            <Tooltip
              contentStyle={{
                background:"#111827",
                borderRadius:14,
                border:"1px solid #27272a",
              }}
            />

            <Bar
              dataKey="assets"
              fill="#3b82f6"
              radius={[8,8,0,0]}
            />

            <Bar
              dataKey="liabilities"
              fill="#ef4444"
              radius={[8,8,0,0]}
            />

          </BarChart>

        </ResponsiveContainer>

      </div>

    </section>

  );
}