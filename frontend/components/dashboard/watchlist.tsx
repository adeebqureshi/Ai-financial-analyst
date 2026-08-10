"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  ArrowUpRight,
  ArrowDownRight,
  Star,
} from "lucide-react";

type Stock = {
  symbol: string;
  company: string;
  price: string;
  change: number;
};

const stocks: Stock[] = [
  {
    symbol: "AAPL",
    company: "Apple",
    price: "$214.78",
    change: 1.42,
  },
  {
    symbol: "MSFT",
    company: "Microsoft",
    price: "$531.44",
    change: 0.91,
  },
  {
    symbol: "NVDA",
    company: "NVIDIA",
    price: "$183.62",
    change: 3.81,
  },
  {
    symbol: "AMZN",
    company: "Amazon",
    price: "$246.02",
    change: -0.72,
  },
  {
    symbol: "TSLA",
    company: "Tesla",
    price: "$318.27",
    change: 2.24,
  },
];

export function Watchlist() {
  return (
    <section className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl">

      <div className="mb-8 flex items-center justify-between">

        <div>

          <h2 className="text-2xl font-bold text-white">
            Watchlist
          </h2>

          <p className="mt-2 text-zinc-500">
            Your tracked companies
          </p>

        </div>

        <button className="rounded-full border border-white/10 bg-white/5 p-3 hover:bg-white/10">

          <Star
            size={18}
            className="text-yellow-400"
          />

        </button>

      </div>

      <div className="space-y-3">

        {stocks.map((stock, index) => {

          const positive = stock.change >= 0;

          return (

            <motion.div

              key={stock.symbol}

              initial={{
                opacity: 0,
                y: 15,
              }}

              animate={{
                opacity: 1,
                y: 0,
              }}

              transition={{
                delay: index * 0.06,
              }}

              whileHover={{
                x: 5,
              }}

              className="flex items-center justify-between rounded-2xl border border-white/5 bg-white/[0.02] px-5 py-4 transition hover:border-blue-500/20 hover:bg-blue-500/5"
            >
              <Link
                href={`/analysis/${stock.symbol}`}
                className="flex w-full items-center justify-between"
              >
                <div>

                  <h3 className="font-semibold text-white">
                    {stock.symbol}
                  </h3>

                  <p className="text-sm text-zinc-500">
                    {stock.company}
                  </p>

                </div>

                <div className="text-right">

                  <div className="font-semibold text-white">
                    {stock.price}
                  </div>

                  <div
                    className={`mt-1 flex items-center justify-end gap-1 text-sm ${
                      positive
                        ? "text-emerald-400"
                        : "text-red-400"
                    }`}
                  >
                    {positive ? (
                      <ArrowUpRight size={14} />
                    ) : (
                      <ArrowDownRight size={14} />
                    )}

                    {Math.abs(stock.change)}%
                  </div>

                </div>
              </Link>
            </motion.div>

          );

        })}

      </div>

    </section>
  );
}