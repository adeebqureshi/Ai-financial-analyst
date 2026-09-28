"use client";

import { createPortal } from "react-dom";
import {
  Children,
  cloneElement,
  useEffect,
  useId,
  useMemo,
  useRef,
  useState,
  type ReactElement,
  type ReactNode,
} from "react";
import { useRouter, usePathname } from "next/navigation";
import {
  ArrowRight,
  CornerDownLeft,
  FileText,
  Search,
  Sparkles,
  X,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { isActivePath, navigationGroups, workspaceItems } from "./nav-items";
import { useCopilot } from "./ai-copilot";

type CommandKind = "navigate" | "analyze" | "ask" | "search-docs" | "report";

type PaletteItem = {
  id: string;
  label: string;
  hint?: string;
  group: string;
  kind: CommandKind;
  href?: string;
  ticker?: string;
  prompt?: string;
};

type Props = {
  children: ReactNode;
};

const QUICK_TICKERS = ["AAPL", "MSFT", "NVDA"];

function tickerFromQuery(query: string): string | null {
  const trimmed = query.trim();

  if (!trimmed || trimmed.length > 6) return null;
  if (!/^[A-Za-z.\-]{1,6}$/.test(trimmed)) return null;

  const symbol = trimmed.toUpperCase();

  return /^[A-Z]{1,5}$/.test(symbol) ? symbol : null;
}

export function CommandPalette({ children }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const inputId = useId();
  const listboxId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const focusRef = useRef<HTMLElement | null>(null);
  const wasOpenRef = useRef(false);
  const router = useRouter();
  const pathname = usePathname();
  const copilot = useCopilot();

  const child = Children.only(children) as ReactElement<{
    onClick?: () => void;
    "aria-haspopup"?: string;
  }>;

  const items = useMemo<PaletteItem[]>(() => {
    const normalized = query.trim();
    const ticker = tickerFromQuery(normalized);
    const dynamic: PaletteItem[] = [];

    if (ticker) {
      dynamic.push({
        id: `analyze-${ticker}`,
        label: `Analyze ${ticker}`,
        hint: "Run the full AI pipeline: valuation, health, risk",
        group: "Ticker",
        kind: "analyze",
        ticker,
        href: `/analysis/${ticker}`,
      });
    }

    if (normalized && !ticker) {
      dynamic.push({
        id: "ask-ai",
        label: `Ask AI: ${normalized}`,
        hint: "Open the copilot and send this question",
        group: "AI",
        kind: "ask",
        prompt: normalized,
      });

      dynamic.push({
        id: "search-docs",
        label: `Search documents for “${normalized}”`,
        hint: "Hybrid vector + keyword retrieval",
        group: "Research",
        kind: "search-docs",
        href: `/search?q=${encodeURIComponent(normalized)}`,
      });
    }

    if (!normalized) {
      for (const symbol of QUICK_TICKERS) {
        dynamic.push({
          id: `quick-${symbol}`,
          label: `Analyze ${symbol}`,
          hint: "Open AI analysis",
          group: "Quick",
          kind: "analyze",
          ticker: symbol,
          href: `/analysis/${symbol}`,
        });
      }
    }

    const navigation: PaletteItem[] = [
      ...navigationGroups.flatMap((group) =>
        group.items.map((item) => ({
          id: `nav-${item.href}`,
          label: item.title,
          hint: item.description,
          group: group.label,
          kind: "navigate" as const,
          href: item.href,
        }))
      ),
      ...workspaceItems.map((item) => ({
        id: `nav-${item.href}`,
        label: item.title,
        group: "Workspace",
        kind: "navigate" as const,
        href: item.href,
      })),
    ];

    return [...dynamic, ...navigation];
  }, [query]);

  const filtered = useMemo(() => {
    const normalized = query.trim().toLowerCase();

    if (!normalized) return items;

    const matches = items.filter(
      (item) =>
        item.label.toLowerCase().includes(normalized) ||
        (item.hint ?? "").toLowerCase().includes(normalized) ||
        (item.group ?? "").toLowerCase().includes(normalized)
    );

    const tickerItem = items.find((item) => item.kind === "analyze");

    if (tickerItem && !matches.includes(tickerItem)) {
      return [tickerItem, ...matches];
    }

    return matches;
  }, [items, query]);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (
        (event.metaKey || event.ctrlKey) &&
        event.key.toLowerCase() === "k"
      ) {
        event.preventDefault();
        setOpen((current) => (current ? false : true));
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, []);

  useEffect(() => {
    if (!open) {
      if (wasOpenRef.current) {
        focusRef.current?.focus();
        focusRef.current = null;
      }

      wasOpenRef.current = false;
      return;
    }

    wasOpenRef.current = true;

    if (!focusRef.current) {
      focusRef.current =
        document.activeElement instanceof HTMLElement
          ? document.activeElement
          : null;
    }

    const frame = window.requestAnimationFrame(() => {
      inputRef.current?.focus();
    });

    return () => window.cancelAnimationFrame(frame);
  }, [open]);

  function openPalette() {
    setOpen(true);
    setQuery("");
    setActiveIndex(0);
  }

  function close() {
    setOpen(false);
    setQuery("");
  }

  function run(item: PaletteItem) {
    if (item.kind === "ask" && item.prompt) {
      close();
      copilot.open({ prompt: item.prompt });
      return;
    }

    close();

    if (item.href) router.push(item.href);
  }

  function onKeyDown(event: React.KeyboardEvent) {
    if (event.key === "Escape") {
      event.preventDefault();
      close();
      return;
    }

    if (event.key === "Tab") {
      const panel = panelRef.current;
      if (!panel) return;

      const focusable = panel.querySelectorAll<HTMLElement>(
        'button, input, a[href], select, textarea, [tabindex]:not([tabindex="-1"])'
      );
      if (focusable.length === 0) return;

      const first = focusable[0];
      const last = focusable[focusable.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }

      return;
    }

    if (filtered.length === 0) return;

    if (event.key === "ArrowDown") {
      event.preventDefault();
      setActiveIndex((index) => (index + 1) % filtered.length);
      return;
    }

    if (event.key === "ArrowUp") {
      event.preventDefault();
      setActiveIndex(
        (index) => (index - 1 + filtered.length) % filtered.length
      );
      return;
    }

    if (event.key === "Enter" && filtered[activeIndex]) {
      event.preventDefault();
      run(filtered[activeIndex]);
    }
  }

  let lastGroup = "";

  return (
    <>
      {cloneElement(child, {
        onClick: () => {
          openPalette();
          child.props.onClick?.();
        },
        "aria-haspopup": "dialog",
      })}

      {open &&
        typeof document !== "undefined" &&
        createPortal(
        <div
          className="fixed inset-0 z-[100] flex items-start justify-center bg-foreground/30 p-3 backdrop-blur-sm motion-safe:animate-in motion-safe:fade-in sm:items-start sm:p-6 sm:pt-[10vh]"
          onMouseDown={(event) => {
            if (event.currentTarget === event.target) close();
          }}
        >
          <div
            ref={panelRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby={inputId}
            onKeyDown={onKeyDown}
            className="flex max-h-[78vh] w-full max-w-2xl flex-col overflow-hidden rounded-2xl border border-border bg-popover text-popover-foreground shadow-overlay motion-safe:animate-in motion-safe:fade-in motion-safe:slide-in-from-top-2 motion-safe:duration-150"
          >
            <div className="flex items-center gap-3 border-b border-border px-4">
              <Search
                size={18}
                className="shrink-0 text-brand"
                aria-hidden="true"
              />
              <input
                ref={inputRef}
                id={inputId}
                type="text"
                value={query}
                onChange={(event) => {
                  setQuery(event.target.value);
                  setActiveIndex(0);
                }}
                onKeyDown={onKeyDown}
                placeholder="Search a company, ask a question, or jump to a workspace…"
                aria-label="Search commands, companies and documents"
                aria-controls={listboxId}
                autoComplete="off"
                spellCheck={false}
                className="h-14 min-w-0 flex-1 bg-transparent text-body text-foreground placeholder:text-subtle-foreground focus:outline-none"
              />
              <button
                type="button"
                onClick={close}
                aria-label="Close command palette"
                className="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <X size={17} aria-hidden="true" />
              </button>
            </div>

            <div
              id={listboxId}
              role="listbox"
              aria-label="Commands and destinations"
              aria-activedescendant={
                filtered[activeIndex]
                  ? `${listboxId}-option-${activeIndex}`
                  : undefined
              }
              className="min-h-0 flex-1 overflow-y-auto p-2"
            >
              {filtered.length === 0 ? (
                <div className="px-3 py-10 text-center">
                  <p className="text-label font-medium text-foreground">
                    No matching commands
                  </p>
                  <p className="mx-auto mt-1.5 max-w-sm text-caption text-muted-foreground">
                    Try a ticker such as AAPL, a question for the copilot, or a
                    workspace name.
                  </p>
                </div>
              ) : (
                filtered.map((item, index) => {
                  const showGroup = item.group !== lastGroup;
                  lastGroup = item.group;

                  return (
                    <div key={item.id}>
                      {showGroup && (
                        <p className="px-3 pb-1 pt-3 text-[11px] font-semibold uppercase tracking-[0.14em] text-subtle-foreground">
                          {item.group}
                        </p>
                      )}

                      <button
                        type="button"
                        id={`${listboxId}-option-${index}`}
                        role="option"
                        aria-selected={activeIndex === index}
                        onMouseEnter={() => setActiveIndex(index)}
                        onClick={() => run(item)}
                        className={cn(
                          "flex w-full items-center gap-3 rounded-lg px-3 py-2.5 text-left",
                          "transition-colors",
                          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                          activeIndex === index
                            ? "bg-accent text-accent-foreground"
                            : "text-foreground hover:bg-muted"
                        )}
                      >
                        <ItemIcon kind={item.kind} active={activeIndex === index} />

                        <span className="min-w-0 flex-1">
                          <span className="block truncate text-body">
                            {item.label}
                          </span>
                          {item.hint && (
                            <span className="mt-0.5 block truncate text-caption text-muted-foreground">
                              {item.hint}
                            </span>
                          )}
                        </span>

                        {item.href && isActivePath(pathname, item.href) && (
                          <span className="shrink-0 text-caption text-muted-foreground">
                            Current page
                          </span>
                        )}
                      </button>
                    </div>
                  );
                })
              )}
            </div>

            <div className="flex flex-wrap items-center justify-between gap-2 border-t border-border bg-surface/60 px-4 py-2.5 text-caption text-muted-foreground">
              <span className="flex items-center gap-3">
                <span>↑↓ to navigate</span>
                <span className="flex items-center gap-1">
                  <CornerDownLeft size={12} aria-hidden="true" />
                  to select
                </span>
                <span>Esc to close</span>
              </span>
              <span className="flex items-center gap-1.5">
                <Sparkles size={12} className="text-brand" aria-hidden="true" />
                Questions route to the AI copilot
              </span>
            </div>
          </div>
        </div>,
        document.body
      )}
    </>
  );
}

function ItemIcon({ kind, active }: { kind: CommandKind; active: boolean }) {
  const Icon =
    kind === "ask"
      ? Sparkles
      : kind === "search-docs"
        ? Search
        : kind === "report"
          ? FileText
          : ArrowRight;

  return (
    <span
      className={cn(
        "flex size-8 shrink-0 items-center justify-center rounded-lg border transition-colors",
        active
          ? "border-brand/30 bg-brand-subtle text-brand"
          : "border-border bg-surface text-muted-foreground"
      )}
      aria-hidden="true"
    >
      <Icon size={15} />
    </span>
  );
}
