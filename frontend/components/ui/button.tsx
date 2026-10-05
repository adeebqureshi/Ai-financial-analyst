"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { ArrowRight, Loader2 } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type TextActionProps = {
  href: string;
  children: ReactNode;
  icon?: ReactNode;
  /** Appends a small arrow that nudges right on hover. */
  arrow?: boolean;
  className?: string;
};

/**
 * Tertiary navigation action — a quiet text link with no container.
 *
 * Use this instead of wrapping a <Link> in border/background/shadow classes
 * for anything that is not the dominant action of a section. Keeping it in one
 * place stops "pseudo-buttons" from accumulating across pages.
 */
export function TextAction({
  href,
  children,
  icon,
  arrow = false,
  className,
}: TextActionProps) {
  return (
    <Link
      href={href}
      className={cn(
        "group/tac inline-flex items-center gap-1.5 rounded-sm text-label font-medium text-brand",
        "underline-offset-4 transition-colors hover:text-foreground",
        "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        "focus-visible:ring-offset-2 focus-visible:ring-offset-background",
        className
      )}
    >
      {icon}
      {children}
      {arrow && (
        <ArrowRight
          size={14}
          className="shrink-0 text-subtle-foreground transition-transform duration-150 group-hover/tac:translate-x-0.5 group-hover/tac:text-brand"
          aria-hidden="true"
        />
      )}
    </Link>
  );
}

export const buttonVariants = cva(
  [
    "relative inline-flex shrink-0 items-center justify-center gap-2",
    "whitespace-nowrap font-medium tracking-[-0.005em]",
    "transition-[background-color,border-color,color,box-shadow,transform] duration-150",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
    "focus-visible:ring-offset-2 focus-visible:ring-offset-background",
    "disabled:pointer-events-none disabled:opacity-55",
    "aria-disabled:pointer-events-none aria-disabled:opacity-55",
    "active:translate-y-px",
    "select-none",
  ].join(" "),
  {
    variants: {
      variant: {
        primary:
          "bg-primary text-primary-foreground shadow-soft hover:bg-primary/90 disabled:bg-muted disabled:text-subtle-foreground disabled:shadow-none",
        secondary:
          "border border-border-strong/70 bg-card text-foreground shadow-soft hover:bg-muted",
        subtle:
          "bg-muted text-foreground hover:bg-accent",
        outline:
          "border border-brand/40 bg-transparent text-brand hover:bg-brand-subtle",
        ghost:
          "text-muted-foreground hover:bg-muted hover:text-foreground",
        danger:
          "bg-destructive text-destructive-foreground shadow-soft hover:bg-destructive/90",
        link:
          "text-brand underline-offset-4 hover:underline",
      },
      size: {
        sm: "h-8 rounded-md px-3 text-caption",
        md: "h-9 rounded-lg px-3.5 text-label",
        // `lg` is the ceiling for primary CTAs — a compact, moderate-radius
        // control. Larger sizes were removed so an oversized pill cannot be
        // reintroduced by accident; pair `lg` with an adjacent input instead.
        lg: "h-10 rounded-lg px-4 text-label",
        icon: "h-9 w-9 rounded-lg",
        "icon-sm": "h-8 w-8 rounded-md",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  }
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  loading?: boolean;
  /**
   * Forwarded to the rendered element (or the Slot when `asChild`). Declared
   * explicitly because React 19 passes `ref` through props, so the existing
   * `...props` spread already forwards it at runtime.
   */
  ref?: React.Ref<HTMLButtonElement>;
}

export function Button({
  className,
  variant,
  size,
  asChild = false,
  loading = false,
  disabled,
  children,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : "button";

  return (
    <Comp
      data-slot="button"
      aria-busy={loading || undefined}
      disabled={asChild ? undefined : disabled || loading}
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    >
      {loading ? (
        <>
          <Loader2
            className="size-4 shrink-0 motion-safe:animate-spin"
            aria-hidden="true"
          />
          {children}
        </>
      ) : (
        children
      )}
    </Comp>
  );
}
