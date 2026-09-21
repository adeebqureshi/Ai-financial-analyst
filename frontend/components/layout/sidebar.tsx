"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  BookOpenText,
  Bot,
  Building2,
  FileText,
  LayoutDashboard,
  Search,
  Sparkles,
  X,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

import { ConnectionStatus } from "./connection-status";
import { ThemeToggle } from "@/components/ui/theme-toggle";

type NavItem = {
  title: string;
  href: string;
  icon: LucideIcon;
};

type NavGroup = {
  label: string;
  items: NavItem[];
};

/* Approved Phase 2 information architecture. */
const groups: NavGroup[] = [
  {
    label: "CO-PILOT",
    items: [
      { title: "Ask AI", href: "/dashboard", icon: Sparkles },
      { title: "Reports", href: "/reports", icon: FileText },
    ],
  },
  {
    label: "RESEARCH",
    items: [
      { title: "Documents", href: "/research", icon: BookOpenText },
      { title: "Search", href: "/search", icon: Search },
    ],
  },
  {
    label: "MARKETS",
    items: [
      { title: "Overview", href: "/dashboard", icon: LayoutDashboard },
      { title: "Screener", href: "/screener", icon: BarChart3 },
      { title: "Compare", href: "/compare", icon: BarChart3 },
    ],
  },
  {
    label: "COMPANY",
    items: [
      { title: "Analyze", href: "/analysis", icon: Building2 },
      { title: "Profile", href: "/company", icon: Building2 },
    ],
  },
];

type Props = {
  open: boolean;
  onClose: () => void;
};

function isActive(pathname: string, href: string) {
  return pathname === href || pathname.startsWith(href + "/");
}

export function Sidebar({ open, onClose }: Props) {
  const pathname = usePathname();

  return (
    <>
      {open && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-foreground/20 backdrop-blur-sm lg:hidden"
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          "fixed left-0 top-0 z-50 flex h-screen w-72 flex-col border-r border-sidebar-border bg-sidebar",
          "transition-transform duration-200",
          open ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
        aria-label="Primary navigation"
      >
        <div className="flex h-16 shrink-0 items-center justify-between border-b border-sidebar-border px-4">
          <Link
            href="/dashboard"
            onClick={onClose}
            className="flex min-w-0 items-center gap-3"
            aria-label="AI Financial Analyst home"
          >
            <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-md bg-brand text-brand-foreground">
              <Bot size={18} aria-hidden="true" />
            </div>
            <div className="text-sm font-semibold leading-tight text-sidebar-foreground">
              AI Financial Analyst
            </div>
          </Link>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close navigation"
            className="rounded-md p-2 text-muted-foreground hover:bg-sidebar-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring lg:hidden"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <nav aria-label="Primary" className="flex-1 overflow-y-auto px-3 py-4">
          {groups.map((group) => (
            <div key={group.label} className="mb-5 last:mb-0">
              <p className="px-2 pb-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                {group.label}
              </p>

              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const active = isActive(pathname, item.href);

                  return (
                    <Link
                      key={item.title}
                      href={item.href}
                      onClick={onClose}
                      aria-current={active ? "page" : undefined}
                      className={cn(
                        "flex items-center gap-2.5 rounded-md px-2 py-1.5 text-sm font-medium transition-colors",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring",
                        active
                          ? "bg-sidebar-accent text-sidebar-accent-foreground"
                          : "text-sidebar-foreground/70 hover:bg-sidebar-accent hover:text-sidebar-foreground"
                      )}
                    >
                      <Icon size={17} aria-hidden="true" />
                      <span>{item.title}</span>
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        <div className="shrink-0 space-y-2 border-t border-sidebar-border p-3">
          <ConnectionStatus />
          <div className="flex items-center justify-between border-t border-sidebar-border pt-2">
            <span className="text-caption text-muted-foreground">Theme</span>
            <ThemeToggle />
          </div>
        </div>
      </aside>
    </>
  );
}
