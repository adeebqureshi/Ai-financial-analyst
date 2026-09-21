"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { Bot, X } from "lucide-react";
import { cn } from "@/lib/utils";

import { ConnectionStatus } from "./connection-status";
import { isActivePath, navigationGroups } from "./nav-items";
import { ThemeToggle } from "@/components/ui/theme-toggle";

type Props = {
  open: boolean;
  onClose: () => void;
};

export function Sidebar({ open, onClose }: Props) {
  const pathname = usePathname();

  // Escape closes the mobile drawer (the desktop rail is always visible).
  useEffect(() => {
    if (!open) return;

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [open, onClose]);

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
        aria-label="Primary navigation"
        className={cn(
          "fixed left-0 top-0 z-50 flex h-screen w-72 flex-col border-r border-sidebar-border bg-sidebar",
          "transition-transform duration-200",
          // `invisible` keeps the closed mobile drawer out of the tab order;
          // it is always visible from `lg` up, where the rail is persistent.
          open
            ? "translate-x-0"
            : "-translate-x-full invisible lg:visible lg:translate-x-0"
        )}
      >
        <div className="flex h-16 shrink-0 items-center justify-between border-b border-sidebar-border px-4">
          <Link
            href="/dashboard"
            onClick={onClose}
            className="flex min-w-0 items-center gap-3 rounded-md focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring"
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
          {navigationGroups.map((group) => (
            <div key={group.label} className="mb-5 last:mb-0">
              <p className="px-2 pb-1.5 text-[11px] font-semibold uppercase tracking-[0.16em] text-muted-foreground">
                {group.label}
              </p>

              <div className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const active = isActivePath(pathname, item.href);

                  return (
                    <Link
                      key={item.href}
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
