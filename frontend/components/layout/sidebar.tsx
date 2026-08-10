"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  LayoutDashboard,
  Building2,
  Bot,
  Briefcase,
  FileText,
  BarChart3,
  Star,
  Settings,
  FolderSearch,
  Search,
} from "lucide-react";

const items = [
  {
    title: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    title: "Companies",
    href: "/company",
    icon: Building2,
  },
  {
    title: "AI Analysis",
    href: "/analysis",
    icon: Bot,
  },
  {
    title: "Portfolio",
    href: "/portfolio",
    icon: Briefcase,
  },
  {
    title: "Reports",
    href: "/reports",
    icon: FileText,
  },
  {
    title: "Research",
    href: "/research",
    icon: FolderSearch,
  },
  {
    title: "Search",
    href: "/search",
    icon: Search,
  },
  {
    title: "Compare",
    href: "/compare",
    icon: BarChart3,
  },
  {
    title: "Watchlist",
    href: "/watchlist",
    icon: Star,
  },
  {
    title: "Settings",
    href: "/settings",
    icon: Settings,
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="fixed left-0 top-0 z-50 flex h-screen w-72 flex-col border-r border-white/10 bg-[#07080D]/80 backdrop-blur-2xl">
      <div className="border-b border-white/10 p-8">
        <h1 className="text-2xl font-bold tracking-tight text-white">
          AI Financial
        </h1>

        <p className="mt-2 text-sm text-zinc-500">
          Enterprise Workspace
        </p>
      </div>

      <nav className="flex-1 space-y-2 p-4">
        {items.map((item) => {
          const Icon = item.icon;

          const active = pathname === item.href;

          return (
            <Link
              key={item.title}
              href={item.href}
            >
              <motion.div
                whileHover={{ x: 4 }}
                className={`flex items-center gap-4 rounded-2xl px-4 py-3 transition-all ${
                  active
                    ? "bg-blue-500/15 text-white"
                    : "text-zinc-500 hover:bg-white/5 hover:text-white"
                }`}
              >
                <Icon size={20} />

                <span>{item.title}</span>
              </motion.div>
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-white/10 p-6">
        <div className="rounded-3xl bg-gradient-to-br from-blue-500/20 to-violet-500/20 p-5">
          <p className="text-xs uppercase tracking-widest text-zinc-400">
            AI Status
          </p>

          <h3 className="mt-2 font-semibold text-white">
            Ready
          </h3>

          <p className="mt-2 text-sm text-zinc-400">
            All AI agents are online.
          </p>
        </div>
      </div>
    </aside>
  );
}