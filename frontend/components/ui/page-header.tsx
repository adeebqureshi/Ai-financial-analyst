import * as React from "react";

import { cn } from "@/lib/utils";

type Props = {

  eyebrow?: React.ReactNode;
  title: React.ReactNode;
  description?: React.ReactNode;

  actions?: React.ReactNode;
  className?: string;

  titleProps?: React.HTMLAttributes<HTMLHeadingElement>;
};


export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className,
  titleProps,
}: Props) {
  return (
    <header
      className={cn(
        "flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between",
        className
      )}
    >
      <div className="min-w-0">
        {eyebrow && (
          <p className="text-caption font-medium uppercase tracking-wide text-subtle-foreground">
            {eyebrow}
          </p>
        )}

        <h1
          {...titleProps}
          className={cn(
            "text-display text-foreground",
            eyebrow ? "mt-1" : undefined,
            titleProps?.className
          )}
        >
          {title}
        </h1>

        {description && (
          <p className="mt-2 max-w-3xl text-body text-muted-foreground">
            {description}
          </p>
        )}
      </div>

      {actions && (
        <div className="flex shrink-0 flex-wrap items-center gap-2">{actions}</div>
      )}
    </header>
  );
}
