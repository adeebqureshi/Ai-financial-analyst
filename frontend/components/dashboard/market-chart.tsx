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

const data = [
  { day: "Mon", value: 102 },
  { day: "Tue", value: 109 },
  { day: "Wed", value: 114 },
  { day: "Thu", value: 110 },
  { day: "Fri", value: 122 },
  { day: "Sat", value: 128 },
  { day: "Sun", value: 137 },
];

export function MarketChart() {
  return (
    <section className="mt-10 rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <p className="text-sm text-zinc-500">
            Market Overview
          </p>

          <h2 className="mt-2 text-3xl font-bold text-white">
            S&P 500 Performance
          </h2>
        </div>

        <div className="rounded-2xl bg-emerald-500/10 px-4 py-2 text-emerald-400">
          +8.42%
        </div>
      </div>

      <div className="h-[420px]">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient
                id="fillGradient"
                x1="0"
                y1="0"
                x2="0"
                y2="1"
              >
                <stop offset="0%" stopColor="#3B82F6" stopOpacity={0.7} />
                <stop offset="100%" stopColor="#3B82F6" stopOpacity={0.02} />
              </linearGradient>
            </defs>

            <CartesianGrid
              stroke="#20242c"
              vertical={false}
            />

            <XAxis
              dataKey="day"
              stroke="#777"
            />

            <YAxis stroke="#777" />

            <Tooltip
              contentStyle={{
                background: "#111827",
                border: "1px solid #27272a",
                borderRadius: 16,
              }}
            />

            <Area
              type="monotone"
              dataKey="value"
              stroke="#3B82F6"
              strokeWidth={4}
              fill="url(#fillGradient)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}