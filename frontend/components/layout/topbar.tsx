"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, Search, UserCircle2 } from "lucide-react";

const titles: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/company": "Companies",
  "/analysis": "AI Analysis",
  "/portfolio": "Portfolio",
  "/reports": "Reports",
  "/compare": "Compare",
  "/watchlist": "Watchlist",
  "/screener": "Screener",
  "/settings": "Settings",
};

export function Topbar() {
  const pathname = usePathname();

  const segments = pathname.split("/").filter(Boolean);

  let title = "Dashboard";

  if (segments.length >= 2) {
    title = titles[`/${segments[0]}`] ?? "Dashboard";
  }

  return (
    <header className="sticky top-0 z-40 flex h-20 items-center justify-between border-b border-white/10 bg-[#05060A]/70 px-10 backdrop-blur-xl">

      <div>
        <h2 className="text-xl font-semibold text-white">
          {title}
        </h2>

        <p className="text-sm text-zinc-500">
          AI Financial Workspace
        </p>
      </div>

      <div className="flex items-center gap-4">

        <Link
          href="/analysis"
          className="flex h-12 w-96 items-center rounded-2xl border border-white/10 bg-white/5 px-4 transition hover:border-blue-500/30"
        >
          <Search
            size={18}
            className="text-zinc-500"
          />

          <span className="ml-3 text-sm text-zinc-500">
            Search company or ask AI...
          </span>
        </Link>

        <button className="rounded-2xl border border-white/10 bg-white/5 p-3 text-zinc-400 hover:text-white">
          <Bell size={20} />
        </button>

        <button className="rounded-full border border-white/10 bg-white/5 p-2">
          <UserCircle2
            size={34}
            className="text-white"
          />
        </button>

      </div>
    </header>
  );
}
