import * as React from "react";

import { cn } from "@/lib/utils";

type Props = {
  eyebrow?: React.ReactNode;
  title: React.ReactNode;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  meta?: React.ReactNode;
  className?: string;
  titleProps?: React.HTMLAttributes<HTMLHeadingElement>;
  compact?: boolean;
};

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  meta,
  className,
  titleProps,
  compact = false,
}: Props) {
  return (
    <header
      className={cn(
        "flex flex-col gap-4 border-b border-border pb-6 sm:flex-row sm:items-end sm:justify-between sm:gap-8",
        compact ? "pb-5" : "pb-7",
        className
      )}
    >
      <div className="min-w-0">
        {eyebrow && (
          <p className="text-caption font-semibold uppercase tracking-[0.16em] text-brand">
            {eyebrow}
          </p>
        )}

        <h1
          {...titleProps}
          className={cn(
            "text-balance text-display text-foreground",
            eyebrow ? "mt-2" : undefined,
            titleProps?.className
          )}
        >
          {title}
        </h1>

        {description && (
          <p className="mt-2.5 max-w-2xl text-body text-muted-foreground">
            {description}
          </p>
        )}

        {meta && (
          <div className="mt-3 flex flex-wrap items-center gap-2 text-caption text-subtle-foreground">
            {meta}
          </div>
        )}
      </div>

      {actions && (
        <div className="flex shrink-0 flex-wrap items-center gap-2">
          {actions}
        </div>
      )}
    </header>
  );
}

export function SectionHeading({
  title,
  description,
  actions,
  className,
  id,
  as: Comp = "h2",
}: {
  title: React.ReactNode;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
  id?: string;
  as?: "h2" | "h3";
}) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-end justify-between gap-x-6 gap-y-2",
        className
      )}
    >
      <div className="min-w-0">
        <Comp id={id} className="text-title text-foreground">
          {title}
        </Comp>
        {description && (
          <p className="mt-1.5 max-w-2xl text-label text-muted-foreground">
            {description}
          </p>
        )}
      </div>

      {actions && (
        <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>
      )}
    </div>
  );
}
