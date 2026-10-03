"use client";

import { useSyncExternalStore } from "react";
import { Menu, Search, Sparkles } from "lucide-react";
import { usePathname } from "next/navigation";

import { Button } from "@/components/ui/button";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { cn } from "@/lib/utils";

import { CommandPalette } from "./command-palette";
import { useCopilot } from "./ai-copilot";
import { sectionForPathname, titleForPathname } from "./nav-items";

type Props = {
  onMenu: () => void;
};

const noopSubscribe = () => () => undefined;

// `navigator.platform` is deprecated but remains the most reliable signal for
// choosing the ⌘ vs Ctrl modifier glyph, so it is read lazily on the client.
function getShortcutLabel(): string {
  if (typeof navigator === "undefined") return "Ctrl K";

  const platform =
    (navigator as Navigator & { userAgentData?: { platform?: string } })
      .userAgentData?.platform ||
    navigator.platform ||
    navigator.userAgent;

  return /mac|iphone|ipad|ipod/i.test(platform) ? "⌘K" : "Ctrl K";
}

export function Topbar({ onMenu }: Props) {
  const pathname = usePathname();
  const title = titleForPathname(pathname);
  const section = sectionForPathname(pathname);
  const copilot = useCopilot();
  const shortcutLabel = useSyncExternalStore(
    noopSubscribe,
    getShortcutLabel,
    () => "Ctrl K"
  );

  return (
    <header className="sticky top-0 z-30 border-b border-border bg-background/85 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-[100rem] items-center gap-3 px-4 sm:px-6 lg:px-8">
        <div className="flex min-w-0 flex-1 items-center gap-2">
          <button
            type="button"
            onClick={onMenu}
            aria-label="Open navigation"
            className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring lg:hidden"
          >
            <Menu size={20} aria-hidden="true" />
          </button>

          <div className="hidden min-w-0 sm:block">
            <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-subtle-foreground">
              {section}
            </p>
            <h1 className="truncate text-subtitle text-foreground">{title}</h1>
          </div>
        </div>

        <div className="flex shrink-0 items-center gap-1.5 sm:gap-2">
          <CommandPalette>
            <button
              type="button"
              aria-label="Open command palette"
              title="Search or ask AI (Ctrl+K)"
              className={cn(
                "group hidden h-10 min-w-0 items-center gap-2.5 rounded-lg border border-border bg-card px-3 text-left text-label text-muted-foreground",
                "shadow-soft transition-colors hover:border-border-strong hover:text-foreground",
                "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                "md:inline-flex md:w-72 lg:w-96"
              )}
            >
              <Search
                size={15}
                className="shrink-0 text-subtle-foreground transition-colors group-hover:text-brand"
                aria-hidden="true"
              />
              <span className="flex-1 truncate">
                Search for a company, ask a question, or upload a document…
              </span>
              <kbd className="hidden shrink-0 rounded border border-border bg-surface px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground lg:inline">
                {shortcutLabel}
              </kbd>
            </button>
          </CommandPalette>

          <div className="md:hidden">
            <CommandPalette>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                aria-label="Open command palette"
              >
                <Search size={18} aria-hidden="true" />
              </Button>
            </CommandPalette>
          </div>

          <Button
            type="button"
            variant={copilot.isOpen ? "subtle" : "secondary"}
            size="sm"
            onClick={() => copilot.toggle()}
            aria-expanded={copilot.isOpen}
            aria-label="Toggle AI copilot"
            className="hidden sm:inline-flex"
          >
            <Sparkles
              size={15}
              className="text-brand"
              aria-hidden="true"
            />
            Ask AI
          </Button>

          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
