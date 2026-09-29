"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect } from "react";
import { ChevronsLeft, LineChart, Plus, X } from "lucide-react";

import { cn } from "@/lib/utils";

import { ConnectionStatus } from "./connection-status";
import {
  isActivePath,
  navigationGroups,
  workspaceItems,
} from "./nav-items";
import { ThemeToggle } from "@/components/ui/theme-toggle";

type Props = {
  open: boolean;
  onClose: () => void;
  collapsed: boolean;
  onToggleCollapsed: () => void;
};

function BrandMark({ size = "md" }: { size?: "md" | "lg" }) {
  return (
    <span
      className={cn(
        "flex shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground",
        size === "lg" ? "size-9" : "size-8"
      )}
      aria-hidden="true"
    >
      <LineChart size={size === "lg" ? 18 : 16} />
    </span>
  );
}

export function Sidebar({
  open,
  onClose,
  collapsed,
  onToggleCollapsed,
}: Props) {
  const pathname = usePathname();

  useEffect(() => {
    if (!open) return;

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose, open]);

  return (
    <>
      {open && (
        <div
          onClick={onClose}
          className="fixed inset-0 z-40 bg-foreground/25 backdrop-blur-[2px] motion-safe:animate-in motion-safe:fade-in lg:hidden"
          aria-hidden="true"
        />
      )}

      <aside
        aria-label="Primary navigation"
        data-state={open ? "open" : "closed"}
        className={cn(
          "fixed left-0 top-0 z-50 flex h-dvh w-[17rem] flex-col",
          "border-r border-sidebar-border bg-sidebar",
          "transition-[width,transform] duration-200 ease-out",
          open ? "translate-x-0" : "-translate-x-full",
          "lg:visible lg:translate-x-0",
          collapsed && "md:w-[4.75rem] lg:w-[4.75rem]"
        )}
      >
        <div
          className={cn(
            "flex h-16 shrink-0 items-center gap-2.5 border-b border-sidebar-border px-4",
            collapsed && "md:justify-center md:px-0"
          )}
        >
          <Link
            href="/dashboard"
            onClick={onClose}
            className="flex min-w-0 items-center gap-2.5 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring"
            aria-label="AI Financial Analyst home"
          >
            <BrandMark />
            <span
              className={cn(
                "min-w-0 text-left transition-opacity",
                collapsed && "md:hidden"
              )}
            >
              <span className="block truncate text-label font-semibold leading-tight text-sidebar-foreground">
                AI Financial Analyst
              </span>
              <span className="block truncate text-caption text-subtle-foreground">
                Research workspace
              </span>
            </span>
          </Link>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close navigation"
            className="ml-auto rounded-lg p-2 text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring lg:hidden"
          >
            <X size={18} aria-hidden="true" />
          </button>
        </div>

        <nav
          aria-label="Primary"
          className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden px-3 py-4"
        >
          {navigationGroups.map((group) => (
            <div key={group.label} className="mb-5 last:mb-0">
              <p
                className={cn(
                  "px-2.5 pb-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-subtle-foreground transition-opacity",
                  collapsed && "md:hidden"
                )}
              >
                {group.label}
              </p>

              <ul className="space-y-0.5">
                {group.items.map((item) => {
                  const Icon = item.icon;
                  const active = isActivePath(pathname, item.href);

                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        onClick={onClose}
                        aria-current={active ? "page" : undefined}
                        title={collapsed ? item.title : undefined}
                        className={cn(
                          "group relative flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-label font-medium",
                          "transition-colors duration-150",
                          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring",
                          collapsed && "md:justify-center md:px-0",
                          active
                            ? "bg-sidebar-accent text-sidebar-accent-foreground"
                            : "text-sidebar-foreground/75 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground"
                        )}
                      >
                        <span
                          aria-hidden="true"
                          className={cn(
                            "absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-full bg-brand transition-opacity",
                            active ? "opacity-100" : "opacity-0"
                          )}
                        />

                        <Icon
                          size={17}
                          className={cn(
                            "shrink-0 transition-colors",
                            active
                              ? "text-brand"
                              : "text-sidebar-foreground/60 group-hover:text-sidebar-foreground"
                          )}
                          aria-hidden="true"
                        />

                        <span
                          className={cn(
                            "truncate transition-opacity",
                            collapsed && "md:hidden"
                          )}
                        >
                          {item.title}
                        </span>
                      </Link>
                    </li>
                  );
                })}
              </ul>
            </div>
          ))}

          <div className="mb-5">
            <p
              className={cn(
                "px-2.5 pb-1.5 text-[11px] font-semibold uppercase tracking-[0.14em] text-subtle-foreground transition-opacity",
                collapsed && "md:hidden"
              )}
            >
              Workspace
            </p>

            <ul className="space-y-0.5">
              {workspaceItems.map((item) => {
                const Icon = item.icon;
                const active = isActivePath(pathname, item.href);

                return (
                  <li key={item.href}>
                    <Link
                      href={item.href}
                      onClick={onClose}
                      aria-current={active ? "page" : undefined}
                      title={collapsed ? item.title : undefined}
                      className={cn(
                        "group relative flex items-center gap-2.5 rounded-lg px-2.5 py-2 text-label font-medium",
                        "transition-colors duration-150",
                        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring",
                        collapsed && "md:justify-center md:px-0",
                        active
                          ? "bg-sidebar-accent text-sidebar-accent-foreground"
                          : "text-sidebar-foreground/75 hover:bg-sidebar-accent/60 hover:text-sidebar-foreground"
                      )}
                    >
                      <Icon
                        size={17}
                        className={cn(
                          "shrink-0",
                          active ? "text-brand" : "text-sidebar-foreground/60"
                        )}
                        aria-hidden="true"
                      />
                      <span
                        className={cn(
                          "truncate transition-opacity",
                          collapsed && "md:hidden"
                        )}
                      >
                        {item.title}
                      </span>
                    </Link>
                  </li>
                );
              })}
            </ul>
          </div>
        </nav>

        <div
          className={cn(
            "shrink-0 space-y-2 border-t border-sidebar-border p-3",
            collapsed && "md:px-2"
          )}
        >
          <Link
            href="/dashboard"
            onClick={onClose}
            className={cn(
              "flex items-center justify-center gap-2 rounded-lg px-3 py-1.5 text-caption font-medium text-brand",
              "transition-colors hover:bg-brand-subtle",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring",
              collapsed && "md:hidden"
            )}
          >
            <Plus size={14} aria-hidden="true" />
            Analyze a ticker
          </Link>

          <div
            className={cn(
              "flex items-center",
              collapsed ? "md:justify-center" : "justify-between"
            )}
          >
            <div className={cn("min-w-0", collapsed && "md:hidden")}>
              <ConnectionStatus />
            </div>

            <div className={cn("hidden items-center gap-0.5 md:flex", collapsed && "md:flex-col")}>
              <ThemeToggle
                className="text-muted-foreground hover:text-foreground"
              />
              <button
                type="button"
                onClick={onToggleCollapsed}
                aria-label={
                  collapsed ? "Expand navigation" : "Collapse navigation"
                }
                aria-pressed={collapsed}
                title={collapsed ? "Expand navigation" : "Collapse navigation"}
                className="inline-flex size-9 items-center justify-center rounded-lg text-muted-foreground transition-colors hover:bg-sidebar-accent hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring"
              >
                <ChevronsLeft
                  size={17}
                  className={cn(
                    "transition-transform duration-200",
                    collapsed && "rotate-180"
                  )}
                  aria-hidden="true"
                />
              </button>
            </div>
          </div>
        </div>
      </aside>
    </>
  );
}
