"use client";

import { motion } from "framer-motion";
import { ArrowRight, Search, Sparkles } from "lucide-react";

const suggestions = [
  "Apple valuation",
  "Tesla DCF",
  "NVIDIA earnings",
  "Microsoft moat",
  "Amazon intrinsic value",
  "Compare AAPL vs MSFT",
];

export function AISearch() {
  return (
    <section className="relative overflow-hidden rounded-[32px] border border-white/10 bg-gradient-to-br from-[#0B1220] via-[#070A12] to-[#05060A] p-10">

      <div className="absolute -left-24 -top-24 h-72 w-72 rounded-full bg-blue-500/10 blur-[120px]" />
      <div className="absolute -right-24 bottom-0 h-80 w-80 rounded-full bg-violet-500/10 blur-[140px]" />

      <div className="relative z-10">

        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: .5 }}
        >

          <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-4 py-2 text-sm text-blue-300">

            <Sparkles size={16} />

            AI Workspace

          </div>

          <h1 className="mt-8 text-6xl font-bold tracking-tight text-white">

            Ask AI about
            <br />
            any public company.

          </h1>

          <p className="mt-6 max-w-3xl text-lg leading-8 text-zinc-400">

            Perform DCF valuation, ratio analysis, Piotroski F Score,
            Altman Z Score, Beneish M Score, intrinsic value calculation,
            risk analysis and portfolio insights instantly.

          </p>

        </motion.div>

        <motion.div

          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: .2 }}

          className="mt-10"

        >

          <div className="flex h-20 items-center rounded-3xl border border-white/10 bg-white/5 px-6 backdrop-blur-xl">

            <Search
              size={24}
              className="text-zinc-500"
            />

            <input

              placeholder="Ask AI anything about Apple, Microsoft, NVIDIA..."

              className="ml-5 flex-1 bg-transparent text-lg text-white outline-none placeholder:text-zinc-500"

            />

            <button className="flex h-14 items-center gap-2 rounded-2xl bg-white px-6 font-medium text-black transition hover:scale-[1.02]">

              Analyze

              <ArrowRight size={18} />

            </button>

          </div>

        </motion.div>

        <div className="mt-8 flex flex-wrap gap-3">

          {suggestions.map((item) => (

            <button

              key={item}

              className="rounded-full border border-white/10 bg-white/5 px-5 py-2 text-sm text-zinc-300 transition hover:border-blue-500/40 hover:bg-blue-500/10 hover:text-white"

            >

              {item}

            </button>

          ))}

        </div>

      </div>

    </section>
  );
}