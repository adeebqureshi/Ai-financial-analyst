"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowUpRight } from "lucide-react";

type Stock = {
  symbol: string;
  company: string;
};

/**
 * Static navigation shortcuts only — no prices or changes are shown because
 * no dashboard endpoint provides them. Live values appear on each company's
 * analysis page, sourced from the backend.
 */
const stocks: Stock[] = [
  { symbol: "AAPL", company: "Apple" },
  { symbol: "MSFT", company: "Microsoft" },
  { symbol: "NVDA", company: "NVIDIA" },
  { symbol: "AMZN", company: "Amazon" },
  { symbol: "TSLA", company: "Tesla" },
];

export function Watchlist() {
  return (
    <section className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl">

      <div className="mb-8">

        <h2 className="text-2xl font-bold text-white">
          Watchlist
        </h2>

        <p className="mt-2 text-zinc-500">
          Shortcut links — open a company for its live AI analysis
        </p>

      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">

        {stocks.map((stock, index) => (
          <motion.div
            key={stock.symbol}
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.06 }}
            whileHover={{ x: 5 }}
            className="rounded-2xl border border-white/5 bg-white/[0.02] transition hover:border-blue-500/20 hover:bg-blue-500/5"
          >
            <Link
              href={`/analysis/${stock.symbol}`}
              className="flex w-full items-center justify-between px-5 py-4"
            >
              <div>
                <h3 className="font-semibold text-white">
                  {stock.symbol}
                </h3>

                <p className="text-sm text-zinc-500">
                  {stock.company}
                </p>
              </div>

              <ArrowUpRight size={16} className="text-zinc-500" />
            </Link>
          </motion.div>
        ))}

      </div>

    </section>
  );
}
