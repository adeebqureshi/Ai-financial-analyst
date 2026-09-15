"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "@/lib/utils";

export const buttonVariants = cva(
  [
    "relative inline-flex items-center justify-center gap-2",
    "whitespace-nowrap font-medium",
    "transition-colors duration-150",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
    "focus-visible:ring-offset-2 focus-visible:ring-offset-background",
    "disabled:pointer-events-none disabled:opacity-50",
    "select-none",
  ].join(" "),
  {
    variants: {
      variant: {
        primary:
          "bg-brand text-brand-foreground hover:bg-brand/90 active:bg-brand/80",
        secondary:
          "border border-border bg-card text-foreground hover:bg-muted",
        ghost: "text-muted-foreground hover:bg-muted hover:text-foreground",
        danger:
          "bg-destructive text-destructive-foreground hover:bg-destructive/90",
      },
      size: {
        sm: "h-8 rounded-md px-3 text-label",
        md: "h-9 rounded-md px-3.5 text-label",
        lg: "h-11 rounded-lg px-5 text-body",
        xl: "h-12 rounded-lg px-6 text-body",
        icon: "h-9 w-9 rounded-md",
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
}

export function Button({
  className,
  variant,
  size,
  asChild = false,
  ...props
}: ButtonProps) {
  const Comp = asChild ? Slot : "button";

  return (
    <Comp
      data-slot="button"
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
}