"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

type CardProps = React.HTMLAttributes<HTMLDivElement> & {
  interactive?: boolean;
  raised?: boolean;
};

export function Card({
  className,
  interactive = false,
  raised = false,
  ...props
}: CardProps) {
  return (
    <div
      data-slot="card"
      className={cn(
        "rounded-xl border border-border",
        raised ? "bg-popover shadow-overlay" : "bg-card shadow-card",
        interactive &&
          "transition-[border-color,box-shadow,background-color] duration-150 hover:border-border-strong hover:shadow-soft",
        className
      )}
      {...props}
    />
  );
}

export function CardHeader({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      data-slot="card-header"
      className={cn(
        "flex flex-wrap items-start justify-between gap-x-4 gap-y-2 border-b border-border px-5 py-3.5 sm:px-6",
        className
      )}
      {...props}
    />
  );
}

export function CardTitle({
  className,
  as: Comp = "h2",
  ...props
}: React.HTMLAttributes<HTMLHeadingElement> & {
  as?: "h1" | "h2" | "h3" | "h4";
}) {
  return (
    <Comp
      data-slot="card-title"
      className={cn("text-subtitle text-foreground", className)}
      {...props}
    />
  );
}

export function CardDescription({
  className,
  ...props
}: React.HTMLAttributes<HTMLParagraphElement>) {
  return (
    <p
      data-slot="card-description"
      className={cn("text-label text-muted-foreground", className)}
      {...props}
    />
  );
}

export function CardBody({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      data-slot="card-body"
      className={cn("px-5 py-5 sm:px-6", className)}
      {...props}
    />
  );
}

export function CardFooter({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      data-slot="card-footer"
      className={cn(
        "flex flex-wrap items-center justify-between gap-3 border-t border-border bg-surface/60 px-5 py-3 sm:px-6",
        className
      )}
      {...props}
    />
  );
}
