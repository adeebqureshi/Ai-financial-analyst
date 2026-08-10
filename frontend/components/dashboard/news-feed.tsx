"use client";

import { motion } from "framer-motion";
import {
  Newspaper,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";

type NewsItem = {
  title: string;
  source: string;
  time: string;
  sentiment: "Positive" | "Negative";
};

const news: NewsItem[] = [
  {
    title: "Apple beats earnings expectations for Q3.",
    source: "Bloomberg",
    time: "12 min ago",
    sentiment: "Positive",
  },
  {
    title: "NVIDIA announces next-generation AI chips.",
    source: "Reuters",
    time: "35 min ago",
    sentiment: "Positive",
  },
  {
    title: "Tesla deliveries decline in Europe.",
    source: "CNBC",
    time: "1 hour ago",
    sentiment: "Negative",
  },
  {
    title: "Microsoft expands Copilot enterprise offerings.",
    source: "WSJ",
    time: "2 hours ago",
    sentiment: "Positive",
  },
];

export function NewsFeed() {
  return (
    <section className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8 backdrop-blur-xl">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">
            Market News
          </h2>

          <p className="mt-2 text-zinc-500">
            Latest financial headlines
          </p>
        </div>

        <Newspaper className="text-blue-400" />
      </div>

      <div className="space-y-4">
        {news.map((item, index) => (
          <motion.div
            key={item.title}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.08 }}
            whileHover={{ x: 4 }}
            className="rounded-2xl border border-white/5 bg-white/[0.02] p-5 transition hover:border-blue-500/20 hover:bg-blue-500/5"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="font-medium leading-6 text-white">
                  {item.title}
                </h3>

                <div className="mt-3 flex items-center gap-3 text-sm text-zinc-500">
                  <span>{item.source}</span>
                  <span>•</span>
                  <span>{item.time}</span>
                </div>
              </div>

              <div
                className={`flex items-center gap-1 rounded-full px-3 py-1 text-xs ${
                  item.sentiment === "Positive"
                    ? "bg-emerald-500/10 text-emerald-400"
                    : "bg-red-500/10 text-red-400"
                }`}
              >
                {item.sentiment === "Positive" ? (
                  <ArrowUpRight size={14} />
                ) : (
                  <ArrowDownRight size={14} />
                )}

                {item.sentiment}
              </div>
            </div>
          </motion.div>
        ))}
      </div>
    </section>
  );
}