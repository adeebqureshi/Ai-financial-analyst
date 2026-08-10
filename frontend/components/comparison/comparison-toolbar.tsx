"use client";

import { Search, Plus, X } from "lucide-react";
import { useState } from "react";

type Props = {
  tickers: string[];
  onAdd: (ticker: string) => void;
  onRemove: (ticker: string) => void;
};

export function ComparisonToolbar({
  tickers,
  onAdd,
  onRemove,
}: Props) {
  const [input, setInput] = useState("");

  function add() {
    onAdd(input);
    setInput("");
  }

  return (

    <section className="rounded-[32px] border border-white/10 bg-white/[0.03] p-8">

      <div className="flex flex-wrap gap-5">

        <div className="flex flex-1 items-center rounded-2xl bg-white/5 px-5">

          <Search
            className="text-zinc-500"
            size={20}
          />

          <input
            value={input}
            onChange={(e) =>
              setInput(e.target.value)
            }
            onKeyDown={(e) => {
              if (e.key === "Enter") add();
            }}
            placeholder="Add company (e.g. TSLA)..."
            className="h-14 flex-1 bg-transparent px-4 outline-none text-white"
          />

        </div>

        <button
          onClick={add}
          className="flex h-14 items-center gap-2 rounded-2xl bg-blue-600 px-6 font-medium text-white transition hover:bg-blue-500"
        >

          <Plus size={18} />

          Add

        </button>

      </div>

      <div className="mt-8 flex flex-wrap gap-3">

        {tickers.map((ticker) => (

          <div
            key={ticker}
            className="flex items-center gap-2 rounded-full bg-blue-600/15 px-5 py-2 text-blue-300"
          >

            {ticker}

            <button
              onClick={() => onRemove(ticker)}
              aria-label={`Remove ${ticker}`}
              className="text-blue-400 transition hover:text-white"
            >
              <X size={14} />
            </button>

          </div>

        ))}

        {tickers.length === 0 && (
          <p className="py-2 text-sm text-zinc-500">
            No companies selected. Add at least one ticker.
          </p>
        )}

      </div>

    </section>

  );

}
