"use client";

import {
  Line,
  LineChart,
  ResponsiveContainer,
  CartesianGrid,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Props = {
  data: {
    year: string;
    revenue: number;
    netIncome: number;
  }[];
};

export function IncomeChart({ data }: Props) {
  return (
    <section className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8">

      <div className="mb-8">

        <h2 className="text-2xl font-bold text-white">
          Revenue vs Net Income
        </h2>

        <p className="mt-2 text-zinc-500">
          Historical profitability
        </p>

      </div>

      <div className="h-[420px]">

        <ResponsiveContainer>

          <LineChart data={data}>

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
                background: "#111827",
                border: "1px solid #27272a",
                borderRadius: 14,
              }}
            />

            <Line
              dataKey="revenue"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={false}
            />

            <Line
              dataKey="netIncome"
              stroke="#10b981"
              strokeWidth={3}
              dot={false}
            />

          </LineChart>

        </ResponsiveContainer>

      </div>

    </section>
  );
}