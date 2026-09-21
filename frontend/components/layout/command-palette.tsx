"use client";

import {
  Children,
  cloneElement,
  useEffect,
  useId,
  useRef,
  useState,
  type ReactElement,
  type ReactNode,
} from "react";
import { useRouter } from "next/navigation";
import { ArrowUpRight, Search, X } from "lucide-react";

import { cn } from "@/lib/utils";

type PaletteItem = {
  label: string;
  href: string;
  group: string;
};

/* The nine approved Phase 2 destinations. */
const ITEMS: PaletteItem[] = [
  { label: "Ask AI", href: "/dashboard", group: "CO-PILOT" },
  { label: "Reports", href: "/reports", group: "CO-PILOT" },
  { label: "Documents", href: "/research", group: "RESEARCH" },
  { label: "Search", href: "/search", group: "RESEARCH" },
  { label: "Overview", href: "/dashboard", group: "MARKETS" },
  { label: "Screener", href: "/screener", group: "MARKETS" },
  { label: "Compare", href: "/compare", group: "MARKETS" },
  { label: "Analyze", href: "/analysis", group: "COMPANY" },
  { label: "Profile", href: "/company", group: "COMPANY" },
];

type Props = {
  children: ReactNode;
};

/**
 * Lightweight, dependency-free command palette.
 *
 * Opened by the wrapped trigger (mouse) or `Cmd/Ctrl+K`. Supports arrow-key
 * navigation, Enter to navigate, Escape to close, click-outside to close, and
 * renders dialog/listbox semantics so screen readers announce it correctly.
 */
export function CommandPalette({ children }: Props) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const inputId = useId();
  const listboxId = useId();
  const inputRef = useRef<HTMLInputElement>(null);
  const router = useRouter();

  const child = Children.only(children) as ReactElement<{
    onClick?: () => void;
    "aria-haspopup"?: string;
  }>;

  const normalized = query.trim().toLowerCase();
  const filtered = normalized
    ? ITEMS.filter((item) => item.label.toLowerCase().includes(normalized))
    : ITEMS;

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (
        (event.metaKey || event.ctrlKey) &&
        event.key.toLowerCase() === "k"
      ) {
        event.preventDefault();
        const next = !open;
        setOpen(next);
        if (next) openPalette();
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  useEffect(() => {
    if (!open) return;

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

  function navigate(href: string) {
    close();
    router.push(href);
  }

  function onKeyDown(event: React.KeyboardEvent) {
    if (event.key === "Escape") {
      event.preventDefault();
      close();
      return;
    }

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
      navigate(filtered[activeIndex].href);
    }
  }

  return (
    <>
      {cloneElement(child, {
        onClick: () => {
          openPalette();
          child.props.onClick?.();
        },
        "aria-haspopup": "dialog",
      })}

      {open && (
        <div
          className="fixed inset-0 z-[100] flex items-start justify-center bg-background/70 p-4 backdrop-blur-sm sm:items-center sm:p-6"
          onMouseDown={(event) => {
            if (event.currentTarget === event.target) close();
          }}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby={inputId}
            className="w-full max-w-lg overflow-hidden rounded-lg border border-border bg-popover text-popover-foreground shadow-overlay"
          >
            <div className="flex items-center gap-3 border-b border-border px-4">
              <Search
                size={17}
                className="shrink-0 text-muted-foreground"
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
                placeholder="Search destinations…"
                aria-label="Filter command palette destinations"
                aria-controls={listboxId}
                className="h-12 min-w-0 flex-1 bg-transparent text-body text-foreground placeholder:text-subtle-foreground focus:outline-none"
              />
              <button
                type="button"
                onClick={close}
                aria-label="Close command palette"
                className="rounded-md p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <X size={17} aria-hidden="true" />
              </button>
            </div>

            <div
              id={listboxId}
              role="listbox"
              aria-label="Navigation destinations"
              aria-activedescendant={
                filtered[activeIndex]
                  ? `${listboxId}-option-${activeIndex}`
                  : undefined
              }
              className="max-h-80 overflow-y-auto p-2"
            >
              {filtered.length === 0 ? (
                <p
                  aria-live="polite"
                  className="px-3 py-6 text-center text-caption text-muted-foreground"
                >
                  No matching destinations.
                </p>
              ) : (
                filtered.map((item, index) => (
                  <button
                    key={`${item.group}-${item.label}`}
                    id={`${listboxId}-option-${index}`}
                    role="option"
                    aria-selected={activeIndex === index}
                    onMouseEnter={() => setActiveIndex(index)}
                    onClick={() => navigate(item.href)}
                    className={cn(
                      "flex w-full items-center gap-3 rounded-md px-3 py-2 text-left text-body",
                      "transition-colors",
                      "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                      activeIndex === index
                        ? "bg-accent text-accent-foreground"
                        : "text-foreground"
                    )}
                  >
                    <span className="min-w-0 flex-1">
                      <span className="block">{item.label}</span>
                      <span className="block text-caption text-muted-foreground">
                        {item.group}
                      </span>
                    </span>
                    <ArrowUpRight
                      size={15}
                      className="shrink-0 text-muted-foreground"
                      aria-hidden="true"
                    />
                  </button>
                ))
              )}
            </div>

            <div className="flex items-center justify-between border-t border-border px-4 py-2 text-caption text-muted-foreground">
              <span>↑↓ navigate</span>
              <span>Enter to open · Esc to close</span>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
