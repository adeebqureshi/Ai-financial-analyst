import * as React from "react";

import { cn } from "@/lib/utils";

type Props = {
  icon?: React.ReactNode;
  title: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
  tone?: "neutral" | "brand";
  compact?: boolean;
};

export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
  tone = "neutral",
  compact = false,
}: Props) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-dashed border-border-strong/70 bg-surface/40 text-center",
        compact ? "px-5 py-6" : "px-6 py-12",
        className
      )}
    >
      {icon && (
        <div
          className={cn(
            "mb-3.5 flex size-10 items-center justify-center rounded-xl",
            tone === "brand"
              ? "bg-brand-subtle text-brand"
              : "bg-muted text-muted-foreground"
          )}
          aria-hidden="true"
        >
          {icon}
        </div>
      )}

      <p className="text-balance text-subtitle text-foreground">{title}</p>

      {description && (
        <p className="mt-1.5 max-w-md text-label leading-relaxed text-muted-foreground">
          {description}
        </p>
      )}

      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}
