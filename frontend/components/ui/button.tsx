"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { Loader2 } from "lucide-react";

import { cn } from "@/lib/utils";

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
          "bg-primary text-primary-foreground shadow-soft hover:bg-primary/90",
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
        lg: "h-11 rounded-lg px-5 text-body",
        xl: "h-12 rounded-xl px-6 text-body",
        icon: "h-9 w-9 rounded-lg",
        "icon-sm": "h-8 w-8 rounded-md",
        "icon-lg": "h-11 w-11 rounded-lg",
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
