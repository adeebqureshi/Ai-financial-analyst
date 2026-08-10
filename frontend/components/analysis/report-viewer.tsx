"use client";

import { useState } from "react";
import { Copy, Check, FileText } from "lucide-react";
import ReactMarkdown from "react-markdown";
import { motion } from "framer-motion";

type Props = {
  report: string;
};

export function ReportViewer({
  report,
}: Props) {
  const [copied, setCopied] =
    useState(false);

  async function copy() {
    await navigator.clipboard.writeText(
      report
    );

    setCopied(true);

    setTimeout(() => {
      setCopied(false);
    }, 2000);
  }

  return (
    <section className="rounded-[36px] border border-white/10 bg-white/[0.03] backdrop-blur-xl">

      <div className="flex items-center justify-between border-b border-white/10 p-6">

        <div className="flex items-center gap-3">

          <FileText className="text-blue-400" />

          <h2 className="text-2xl font-bold text-white">
            AI Investment Report
          </h2>

        </div>

        <button
          onClick={copy}
          className="rounded-xl border border-white/10 bg-white/5 p-3 transition hover:bg-white/10"
        >
          {copied ? (
            <Check
              size={18}
              className="text-emerald-400"
            />
          ) : (
            <Copy
              size={18}
              className="text-zinc-300"
            />
          )}
        </button>

      </div>

      <motion.div
        initial={{
          opacity: 0,
        }}
        animate={{
          opacity: 1,
        }}
        className="prose prose-invert max-w-none p-8 prose-headings:text-white prose-p:text-zinc-300 prose-strong:text-white prose-code:text-blue-300 prose-pre:bg-black/30 prose-li:text-zinc-300"
      >
        <ReactMarkdown>
          {report}
        </ReactMarkdown>
      </motion.div>

    </section>
  );
}