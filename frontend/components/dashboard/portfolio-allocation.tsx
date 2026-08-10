"use client";

import { Cell, Pie, PieChart, ResponsiveContainer } from "recharts";

const data = [
  { name: "Technology", value: 46 },
  { name: "Healthcare", value: 18 },
  { name: "Finance", value: 14 },
  { name: "Energy", value: 12 },
  { name: "Others", value: 10 },
];

const COLORS = [
  "#3B82F6",
  "#8B5CF6",
  "#10B981",
  "#F59E0B",
  "#64748B",
];

export function PortfolioAllocation() {
  return (
    <section className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl">

      <div className="mb-8">
        <h2 className="text-2xl font-bold text-white">
          Portfolio Allocation
        </h2>

        <p className="mt-2 text-zinc-500">
          Sector diversification
        </p>
      </div>

      <div className="grid gap-8 lg:grid-cols-[300px_1fr]">

        <div className="h-[280px]">

          <ResponsiveContainer width="100%" height="100%">

            <PieChart>

              <Pie
                data={data}
                innerRadius={80}
                outerRadius={115}
                paddingAngle={4}
                dataKey="value"
              >

                {data.map((entry, index) => (
                  <Cell
                    key={entry.name}
                    fill={COLORS[index]}
                  />
                ))}

              </Pie>

            </PieChart>

          </ResponsiveContainer>

        </div>

        <div className="space-y-5">

          {data.map((item, index) => (

            <div
              key={item.name}
              className="flex items-center justify-between rounded-2xl border border-white/5 bg-white/[0.02] px-5 py-4"
            >

              <div className="flex items-center gap-4">

                <div
                  className="h-4 w-4 rounded-full"
                  style={{
                    background: COLORS[index],
                  }}
                />

                <span className="text-white">
                  {item.name}
                </span>

              </div>

              <span className="font-semibold text-white">
                {item.value}%
              </span>

            </div>

          ))}

        </div>

      </div>

    </section>
  );
}