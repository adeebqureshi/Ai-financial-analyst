"use client";

import { Search, Plus } from "lucide-react";
import { useState } from "react";

const defaults = [
  "AAPL",
  "MSFT",
  "NVDA",
  "GOOGL",
];

export function ComparisonToolbar() {

  const [tickers] =
    useState(defaults);

  return (

    <section className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8">

      <div className="flex flex-wrap gap-5">

        <div className="flex flex-1 items-center rounded-2xl bg-white/5 px-5">

          <Search
            className="text-zinc-500"
            size={20}
          />

          <input
            placeholder="Add company..."
            className="h-14 flex-1 bg-transparent px-4 outline-none text-white"
          />

        </div>

        <button className="flex h-14 items-center gap-2 rounded-2xl bg-blue-600 px-6 font-medium">

          <Plus size={18} />

          Add

        </button>

      </div>

      <div className="mt-8 flex flex-wrap gap-3">

        {tickers.map((ticker) => (

          <div
            key={ticker}
            className="rounded-full bg-blue-600/15 px-5 py-2 text-blue-300"
          >
            {ticker}
          </div>

        ))}

      </div>

    </section>

  );

}