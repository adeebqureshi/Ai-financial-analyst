"use client";

import { useEffect, useId, useRef, useState } from "react";
import Link from "next/link";
import { MoreHorizontal, Trash2 } from "lucide-react";

import { cn } from "@/lib/utils";

type Props = {
  sessionId: string;
  /** Where "Open session" navigates to. */
  href: string;
  /** Human label for the session, used to build accessible control names. */
  sessionLabel: string;
  onRequestDelete: () => void;
  /** Disables the control while a delete for this row is in flight. */
  busy?: boolean;
};

/**
 * Per-session overflow menu ("Open session" / "Delete").
 *
 * The trigger is a real `<button>` that is a *sibling* of the row's link rather
 * than a descendant — nesting a button inside an anchor is invalid HTML and
 * makes the row ambiguous for screen-reader and keyboard users.
 *
 * Follows the disclosure idiom already used by `TickerExamplesMenu`: state plus
 * `aria-expanded` / `aria-haspopup` / `aria-controls`, closed on Escape, on blur
 * leaving the wrapper, and on selecting an item.
 */
export function SessionActionsMenu({
  sessionId,
  href,
  sessionLabel,
  onRequestDelete,
  busy = false,
}: Props) {
  const [open, setOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const menuId = useId();

  // Close when focus leaves the wrapper, so the menu can never be orphaned.
  useEffect(() => {
    if (!open) return;

    function onFocusIn(event: FocusEvent) {
      if (!wrapperRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    document.addEventListener("focusin", onFocusIn);
    return () => document.removeEventListener("focusin", onFocusIn);
  }, [open]);

  return (
    <div ref={wrapperRef} className="relative shrink-0">
      <button
        ref={triggerRef}
        type="button"
        aria-expanded={open}
        aria-haspopup="menu"
        aria-controls={open ? menuId : undefined}
        aria-label={`Actions for ${sessionLabel}`}
        disabled={busy}
        onClick={() => setOpen((value) => !value)}
        onKeyDown={(event) => {
          if (event.key === "Escape" && open) {
            event.preventDefault();
            setOpen(false);
          }
        }}
        className={cn(
          "flex size-7 items-center justify-center rounded-md text-muted-foreground transition-colors",
          "hover:bg-muted hover:text-foreground",
          "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          open && "bg-muted text-foreground",
          busy && "cursor-progress opacity-60"
        )}
      >
        <MoreHorizontal size={15} aria-hidden="true" />
      </button>

      {open && (
        <div
          id={menuId}
          role="menu"
          aria-label={`Actions for ${sessionLabel}`}
          className={cn(
            "absolute right-0 top-full z-30 mt-1 w-44 overflow-hidden rounded-xl border border-border bg-popover p-1 shadow-overlay",
            // On narrow viewports a right-aligned 11rem menu still fits, but pin
            // it inward so it can never push past the viewport edge.
            "max-w-[min(11rem,calc(100vw-2rem))]"
          )}
        >
          <Link
            href={href}
            role="menuitem"
            onClick={() => setOpen(false)}
            className="flex w-full items-center rounded-lg px-2.5 py-2 text-left text-caption text-foreground transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            Open session
          </Link>

          <button
            type="button"
            role="menuitem"
            data-session-id={sessionId}
            onClick={() => {
              setOpen(false);
              onRequestDelete();
            }}
            className="flex w-full items-center gap-2 rounded-lg px-2.5 py-2 text-left text-caption text-loss transition-colors hover:bg-loss-subtle focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Trash2 size={13} aria-hidden="true" />
            Delete
          </button>
        </div>
      )}
    </div>
  );
}