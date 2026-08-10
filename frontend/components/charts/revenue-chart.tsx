"use client";

import {
  Area,
  AreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type Props = {
  revenue: number[];
};

export function RevenueChart({
  revenue,
}: Props) {
  const data = revenue.map((value, index) => ({
    year: `FY${2020 + index}`,
    revenue: value,
  }));

  return (
    <section className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl">

      <div className="mb-8">

        <h2 className="text-2xl font-bold text-white">
          Revenue Trend
        </h2>

        <p className="mt-2 text-zinc-500">
          Historical revenue growth
        </p>

      </div>

      <div className="h-[420px]">

        <ResponsiveContainer width="100%" height="100%">

          <AreaChart data={data}>

            <defs>

              <linearGradient
                id="revenueFill"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >

                <stop
                  offset="0%"
                  stopColor="#3b82f6"
                  stopOpacity={0.65}
                />

                <stop
                  offset="100%"
                  stopColor="#3b82f6"
                  stopOpacity={0}
                />

              </linearGradient>

            </defs>

            <CartesianGrid
              stroke="#20242c"
              vertical={false}
            />

            <XAxis
              dataKey="year"
              stroke="#666"
            />

            <YAxis stroke="#666" />

            <Tooltip
              contentStyle={{
                background: "#0f172a",
                borderRadius: 16,
                border: "1px solid #27272a",
              }}
            />

            <Area
              type="monotone"
              dataKey="revenue"
              stroke="#3b82f6"
              strokeWidth={3}
              fill="url(#revenueFill)"
            />

          </AreaChart>

        </ResponsiveContainer>

      </div>

    </section>
  );
}