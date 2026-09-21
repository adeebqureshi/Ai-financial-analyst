"use client";

import { Command, Menu, Search } from "lucide-react";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { CommandPalette } from "./command-palette";

const titles: Record<string, string> = {
  "/dashboard": "Overview",
  "/company": "Profile",
  "/analysis": "Analyze",
  "/compare": "Compare",
  "/portfolio": "Portfolio",
  "/reports": "Reports",
  "/research": "Documents",
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
  const title =
    segments.length >= 1 ? titles[`/${segments[0]}`] ?? "Workspace" : "Workspace";

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-background/95 px-4 backdrop-blur-sm sm:px-6 lg:px-8">
      <div className="flex min-w-0 items-center gap-3">
        <button
          type="button"
          onClick={onMenu}
          aria-label="Open navigation"
          className="rounded-md p-2 text-muted-foreground hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring lg:hidden"
        >
          <Menu size={20} aria-hidden="true" />
        </button>

        <div className="min-w-0">
          <h1 className="truncate text-title text-foreground">{title}</h1>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-2">
        <CommandPalette>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            aria-label="Open command palette"
            title="Open command palette (Ctrl+K)"
            className="hidden min-w-64 justify-between text-muted-foreground md:inline-flex"
          >
            <span className="inline-flex items-center gap-2">
              <Search size={15} aria-hidden="true" />
              Search or navigate…
            </span>
            <kbd className="rounded border border-border bg-background px-1.5 text-[11px] text-muted-foreground">
              ⌘K
            </kbd>
          </Button>
        </CommandPalette>

        <div className="md:hidden">
          <CommandPalette>
            <Button
              type="button"
              variant="ghost"
              size="icon-sm"
              aria-label="Open command palette"
            >
              <Command size={17} aria-hidden="true" />
            </Button>
          </CommandPalette>
        </div>

        <ThemeToggle />
      </div>
    </header>
  );
}
