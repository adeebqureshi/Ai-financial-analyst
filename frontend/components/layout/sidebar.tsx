"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { motion } from "framer-motion";
import {
  Bot,
  BookOpen,
  LayoutDashboard,
  LineChart,
  Scale,
  Briefcase,
  FileText,
  Search,
  Star,
  Settings,
  X,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/lib/utils";

type NavItem = {
  title: string;
  href: string;
  icon: LucideIcon;
};

type NavGroup = {
  label: string;
  items: NavItem[];
};

const groups: NavGroup[] = [
  {
    label: "AI Financial Agent",
    items: [
      {
        title: "Ask AI",
        href: "/",
        icon: Bot,
      },
    ],
  },
  {
    label: "Research",
    items: [
      {
        title: "Documents",
        href: "/research",
        icon: BookOpen,
      },
      {
        title: "Search",
        href: "/search",
        icon: Search,
      },
    ],
  },
  {
    label: "Analysis",
    items: [
      {
        title: "Dashboard",
        href: "/dashboard",
        icon: LayoutDashboard,
      },
      {
        title: "Company Analysis",
        href: "/analysis",
        icon: LineChart,
      },
      {
        title: "Compare",
        href: "/compare",
        icon: Scale,
      },
      {
        title: "Portfolio",
        href: "/portfolio",
        icon: Briefcase,
      },
      {
        title: "Watchlist",
        href: "/watchlist",
        icon: Star,
      },
    ],
  },
  {
    label: "Output",
    items: [
      {
        title: "Reports",
        href: "/reports",
        icon: FileText,
      },
    ],
  },
];

type Props = {
  open: boolean;
  onClose: () => void;
};

export function Sidebar({ open, onClose }: Props) {
  const pathname = usePathname();

  function isActive(href: string) {
    if (href === "/") return pathname === "/";

    return (
      pathname === href || pathname.startsWith(href + "/")
    );
  }

  return (
    <>
      {/* Mobile overlay */}
      {open && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-black/60 backdrop-blur-sm lg:hidden"
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          "fixed left-0 top-0 z-50 flex h-screen w-72 flex-col border-r border-white/10 bg-[#07080D]/95 backdrop-blur-2xl",
          "transition-transform duration-300",
          open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
        aria-label="Primary navigation"
      >
        <div className="flex items-center justify-between border-b border-white/10 p-6">
          <Link
            href="/"
            onClick={onClose}
            className="flex items-center gap-3"
          >
            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-indigo-500">
              <Bot size={22} className="text-white" />
            </div>

            <div>
              <h1 className="text-sm font-bold leading-tight tracking-tight text-white">
                AI Financial
                <br />
                Research Agent
              </h1>
            </div>
          </Link>

          <button
            onClick={onClose}
            aria-label="Close navigation"
            className="rounded-xl border border-white/10 p-2 text-zinc-400 hover:text-white lg:hidden"
          >
            <X size={18} />
          </button>
        </div>

        <nav className="flex-1 space-y-6 overflow-y-auto p-4">
          {groups.map((group) => (
            <div key={group.label}>
              <p className="px-4 pb-2 text-[11px] font-medium uppercase tracking-[0.2em] text-zinc-600">
                {group.label}
              </p>

              <div className="space-y-1">
                {group.items.map((item) => {
                  const Icon = item.icon;

                  const active = isActive(item.href);

                  return (
                    <Link
                      key={item.title}
                      href={item.href}
                      onClick={onClose}
                    >
                      <motion.div
                        whileHover={{ x: 3 }}
                        className={cn(
                          "flex items-center gap-4 rounded-2xl px-4 py-3 transition-all",
                          active
                            ? "bg-blue-500/15 text-white"
                            : "text-zinc-500 hover:bg-white/5 hover:text-white"
                        )}
                      >
                        <Icon size={20} />

                        <span>{item.title}</span>

                        {active && (
                          <span className="ml-auto h-1.5 w-1.5 rounded-full bg-blue-400" />
                        )}
                      </motion.div>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="border-t border-white/10 p-4">
          <Link
            href="/settings"
            onClick={onClose}
            className={cn(
              "flex items-center gap-4 rounded-2xl px-4 py-3 transition-all",
              isActive("/settings")
                ? "bg-blue-500/15 text-white"
                : "text-zinc-500 hover:bg-white/5 hover:text-white"
            )}
          >
            <Settings size={20} />

            <span>Settings</span>
          </Link>

          <div className="mt-3 rounded-3xl bg-gradient-to-br from-blue-500/20 to-violet-500/20 p-5">
            <p className="text-xs uppercase tracking-widest text-zinc-400">
              Agent Status
            </p>

            <h3 className="mt-2 flex items-center gap-2 font-semibold text-white">
              <span className="h-2 w-2 rounded-full bg-emerald-400" />
              Ready
            </h3>

            <p className="mt-2 text-sm text-zinc-400">
              Ask a research question to start.
            </p>
          </div>
        </div>
      </aside>
    </>
  );
}
