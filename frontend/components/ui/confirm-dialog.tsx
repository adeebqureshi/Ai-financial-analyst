"use client";

import { useEffect, useId, useRef, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { AlertTriangle } from "lucide-react";

import { Button } from "@/components/ui/button";

type Props = {
  open: boolean;
  title: string;
  description: ReactNode;
  confirmLabel?: string;
  cancelLabel?: string;
  /** Puts the dialog into a pending, un-dismissable state while work runs. */
  pending?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
};

/**
 * Modal confirmation for destructive actions.
 *
 * Built on the same hand-rolled portal/focus model as the command palette, so
 * no dialog dependency is introduced. Accessibility contract:
 *
 * - `role="dialog"` + `aria-modal` + `aria-labelledby` / `aria-describedby`, so
 *   the heading and body are announced as the dialog's name and description.
 * - Escape and a backdrop click both cancel, except while `pending` — a request
 *   already in flight must not be abandoned halfway.
 * - Focus moves to the panel on open and returns to the previously focused
 *   element on close, and Tab is trapped inside the dialog.
 *
 * The confirm button is never the autofocused element: on a destructive dialog
 * the safe action should hold focus first, so a stray Enter cannot delete.
 */
export function ConfirmDialog({
  open,
  title,
  description,
  confirmLabel = "Delete",
  cancelLabel = "Cancel",
  pending = false,
  onConfirm,
  onCancel,
}: Props) {
  const titleId = useId();
  const descriptionId = useId();

  const panelRef = useRef<HTMLDivElement>(null);
  const cancelRef = useRef<HTMLButtonElement>(null);
  const restoreFocusRef = useRef<HTMLElement | null>(null);

  // Remember what opened the dialog so focus can be handed back on close.
  useEffect(() => {
    if (!open) return;

    restoreFocusRef.current =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;

    cancelRef.current?.focus();

    return () => {
      restoreFocusRef.current?.focus?.();
    };
  }, [open]);

  useEffect(() => {
    if (!open || typeof document === "undefined") return;

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [open]);

  if (!open || typeof document === "undefined") return null;

  function handleKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    if (event.key === "Escape") {
      event.preventDefault();

      // Do not let the user dismiss a dialog whose request is still running.
      if (!pending) onCancel();
      return;
    }

    if (event.key !== "Tab") return;

    const panel = panelRef.current;
    if (!panel) return;

    const focusable = panel.querySelectorAll<HTMLElement>(
      'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'
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
  }

  return createPortal(
    <div
      className="fixed inset-0 z-[110] flex items-center justify-center bg-foreground/30 p-4 backdrop-blur-sm motion-safe:animate-in motion-safe:fade-in"
      onMouseDown={(event) => {
        if (event.currentTarget === event.target && !pending) onCancel();
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        aria-busy={pending || undefined}
        onKeyDown={handleKeyDown}
        className="w-full max-w-md overflow-hidden rounded-2xl border border-border bg-popover text-popover-foreground shadow-overlay motion-safe:animate-in motion-safe:fade-in motion-safe:zoom-in-95 motion-safe:duration-150"
      >
        <div className="flex gap-3.5 p-5">
          <span
            className="flex size-9 shrink-0 items-center justify-center rounded-xl bg-loss-subtle text-loss ring-1 ring-loss/20"
            aria-hidden="true"
          >
            <AlertTriangle size={18} />
          </span>

          <div className="min-w-0 flex-1">
            <h2
              id={titleId}
              className="text-subtitle font-semibold tracking-[-0.01em] text-foreground"
            >
              {title}
            </h2>
            <div
              id={descriptionId}
              className="mt-1.5 text-label leading-relaxed text-muted-foreground"
            >
              {description}
            </div>
          </div>
        </div>

        <div className="flex flex-col-reverse gap-2 border-t border-border bg-surface/40 px-5 py-3.5 sm:flex-row sm:justify-end">
          <Button
            ref={cancelRef}
            type="button"
            variant="secondary"
            size="md"
            onClick={onCancel}
            disabled={pending}
          >
            {cancelLabel}
          </Button>

          <Button
            type="button"
            variant="danger"
            size="md"
            onClick={onConfirm}
            loading={pending}
            // `loading` already disables the button; this guards a double click
            // landing in the same tick before React re-renders.
            disabled={pending}
            aria-busy={pending || undefined}
          >
            {pending ? "Deleting..." : confirmLabel}
          </Button>
        </div>
      </div>
    </div>,
    document.body
  );
}