"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, Menu, Search, UserCircle2 } from "lucide-react";

const titles: Record<string, string> = {
  "/": "Ask AI",
  "/dashboard": "Financial Workspace",
  "/company": "Companies",
  "/analysis": "Company Analysis",
  "/compare": "Compare",
  "/comparison": "Compare",
  "/portfolio": "Portfolio",
  "/reports": "Reports",
  "/research": "Research",
  "/search": "Search",
  "/watchlist": "Watchlist",
  "/screener": "Screener",
  "/settings": "Settings",
};

type Props = {
  onMenu: () => void;
};

export function Topbar({ onMenu }: Props) {
  const pathname = usePathname();

  const segments = pathname.split("/").filter(Boolean);

  let title = "Ask AI";

  if (segments.length >= 1) {
    title = titles[`/${segments[0]}`] ?? "Ask AI";
  }

  if (pathname.startsWith("/analysis/") && segments.length >= 2) {
    title = "Company Analysis";
  }

  return (
    <header className="sticky top-0 z-30 flex h-20 items-center justify-between border-b border-white/10 bg-[#05060A]/70 px-4 backdrop-blur-xl sm:px-6 lg:px-10">
      <div className="flex items-center gap-4">
        <button
          onClick={onMenu}
          aria-label="Open navigation"
          className="rounded-2xl border border-white/10 bg-white/5 p-3 text-zinc-300 hover:text-white lg:hidden"
        >
          <Menu size={20} />
        </button>

        <div>
          <h2 className="text-xl font-semibold text-white">
            {title}
          </h2>

          <p className="text-sm text-zinc-500">
            AI Financial Research Workspace
          </p>
        </div>
      </div>

      <div className="flex items-center gap-3">
        <Link
          href="/"
          className="hidden h-12 w-64 items-center rounded-2xl border border-white/10 bg-white/5 px-4 transition hover:border-blue-500/30 md:flex lg:w-96"
        >
          <Search
            size={18}
            className="text-zinc-500"
          />

          <span className="ml-3 truncate text-sm text-zinc-500">
            Ask the AI financial agent...
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
