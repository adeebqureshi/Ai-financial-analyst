"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  BrainCircuit,
  Building2,
  ChevronDown,
  FileText,
  LayoutDashboard,
  LineChart,
  Settings,
  Sparkles,
  Star,
  Wallet,
} from "lucide-react";

const navigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Markets",
    href: "/markets",
    icon: LineChart,
  },
  {
    name: "Companies",
    href: "/company",
    icon: Building2,
  },
  {
    name: "Portfolio",
    href: "/portfolio",
    icon: Wallet,
  },
  {
    name: "AI Analysis",
    href: "/analysis",
    icon: BrainCircuit,
  },
  {
    name: "Reports",
    href: "/reports",
    icon: FileText,
  },
];

const tools = [
  {
    name: "Watchlist",
    href: "/watchlist",
    icon: Star,
  },
  {
    name: "Analytics",
    href: "/analytics",
    icon: BarChart3,
  },
];

export default function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/dashboard") {
      return pathname === "/dashboard";
    }

    return pathname.startsWith(href);
  };

  return (
    <aside className="fixed inset-y-0 left-0 z-50 hidden w-[250px] flex-col border-r border-white/[0.07] bg-[#07080b] lg:flex">
      {/* Logo */}
      <div className="flex h-[76px] items-center border-b border-white/[0.06] px-6">
        <Link
          href="/dashboard"
          className="flex items-center gap-3"
        >
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-white text-black">
            <Sparkles size={18} />
          </div>

          <div>
            <div className="text-sm font-semibold tracking-tight text-white">
              AI Financial
            </div>

            <div className="text-[10px] font-medium uppercase tracking-[0.2em] text-zinc-600">
              Analyst
            </div>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <div className="flex-1 overflow-y-auto px-3 py-6">
        <p className="mb-3 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-zinc-600">
          Workspace
        </p>

        <nav className="space-y-1">
          {navigation.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);

            return (
              <Link
                key={item.name}
                href={item.href}
                className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all ${
                  active
                    ? "bg-white/[0.08] text-white"
                    : "text-zinc-500 hover:bg-white/[0.04] hover:text-zinc-200"
                }`}
              >
                <Icon
                  size={17}
                  strokeWidth={active ? 2 : 1.7}
                  className={
                    active
                      ? "text-white"
                      : "text-zinc-600 group-hover:text-zinc-300"
                  }
                />

                <span>{item.name}</span>

                {active && (
                  <span className="ml-auto h-1.5 w-1.5 rounded-full bg-blue-400" />
                )}
              </Link>
            );
          })}
        </nav>

        <p className="mb-3 mt-8 px-3 text-[10px] font-semibold uppercase tracking-[0.18em] text-zinc-600">
          Tools
        </p>

        <nav className="space-y-1">
          {tools.map((item) => {
            const Icon = item.icon;
            const active = isActive(item.href);

            return (
              <Link
                key={item.name}
                href={item.href}
                className={`group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition-all ${
                  active
                    ? "bg-white/[0.08] text-white"
                    : "text-zinc-500 hover:bg-white/[0.04] hover:text-zinc-200"
                }`}
              >
                <Icon
                  size={17}
                  className={
                    active
                      ? "text-white"
                      : "text-zinc-600 group-hover:text-zinc-300"
                  }
                />

                <span>{item.name}</span>
              </Link>
            );
          })}
        </nav>
      </div>

      {/* Bottom */}
      <div className="border-t border-white/[0.06] p-3">
        <Link
          href="/settings"
          className="flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-zinc-500 transition hover:bg-white/[0.04] hover:text-zinc-200"
        >
          <Settings size={17} />
          Settings
        </Link>

        <div className="mt-2 flex items-center gap-3 rounded-xl bg-white/[0.03] p-3">
          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-blue-400 to-violet-500 text-xs font-semibold text-white">
            AQ
          </div>

          <div className="min-w-0 flex-1">
            <p className="truncate text-xs font-medium text-white">
              Adeeb Qureshi
            </p>

            <p className="truncate text-[10px] text-zinc-600">
              Personal workspace
            </p>
          </div>

          <ChevronDown
            size={14}
            className="text-zinc-600"
          />
        </div>
      </div>
    </aside>
  );
}