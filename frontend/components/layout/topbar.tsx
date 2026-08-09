"use client";

import {
  Bell,
  Command,
  Menu,
  Search,
  Sparkles,
} from "lucide-react";

export default function Topbar() {
  return (
    <header className="sticky top-0 z-40 flex h-[76px] items-center border-b border-white/[0.06] bg-[#07080b]/90 px-5 backdrop-blur-xl lg:px-8">
      {/* Mobile menu */}
      <button
        type="button"
        aria-label="Open menu"
        className="rounded-lg p-2 text-zinc-500 hover:bg-white/[0.05] hover:text-white lg:hidden"
      >
        <Menu size={20} />
      </button>

      {/* Search */}
      <button
        type="button"
        className="group hidden h-10 w-[360px] items-center gap-3 rounded-xl border border-white/[0.07] bg-white/[0.025] px-3.5 text-left transition hover:border-white/[0.12] hover:bg-white/[0.04] md:flex"
      >
        <Search
          size={16}
          className="text-zinc-600 group-hover:text-zinc-400"
        />

        <span className="flex-1 text-xs text-zinc-600">
          Search companies, markets, filings...
        </span>

        <span className="flex items-center gap-1 rounded-md border border-white/[0.08] px-1.5 py-1 text-[10px] text-zinc-600">
          <Command size={10} />
          K
        </span>
      </button>

      {/* Right side */}
      <div className="ml-auto flex items-center gap-2">
        {/* AI status */}
        <div className="hidden items-center gap-2 rounded-lg border border-emerald-400/10 bg-emerald-400/[0.04] px-3 py-2 sm:flex">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 shadow-[0_0_8px_rgba(52,211,153,0.8)]" />

          <span className="text-[11px] text-emerald-400">
            AI Online
          </span>
        </div>

        {/* AI assistant */}
        <button
          type="button"
          aria-label="AI assistant"
          className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/[0.07] bg-white/[0.025] text-zinc-500 transition hover:border-white/[0.12] hover:bg-white/[0.05] hover:text-white"
        >
          <Sparkles size={16} />
        </button>

        {/* Notifications */}
        <button
          type="button"
          aria-label="Notifications"
          className="relative flex h-9 w-9 items-center justify-center rounded-xl border border-white/[0.07] bg-white/[0.025] text-zinc-500 transition hover:border-white/[0.12] hover:bg-white/[0.05] hover:text-white"
        >
          <Bell size={16} />

          <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-blue-400 ring-2 ring-[#07080b]" />
        </button>

        {/* Profile */}
        <button
          type="button"
          className="ml-1 flex items-center gap-2 rounded-xl border border-white/[0.07] bg-white/[0.025] p-1.5 pr-3 transition hover:bg-white/[0.05]"
        >
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-gradient-to-br from-blue-400 to-violet-500 text-[10px] font-semibold text-white">
            AQ
          </div>

          <span className="hidden text-xs text-zinc-400 lg:block">
            Adeeb
          </span>
        </button>
      </div>
    </header>
  );
}