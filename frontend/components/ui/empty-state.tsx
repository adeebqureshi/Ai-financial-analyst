import * as React from "react";

import { cn } from "@/lib/utils";

type Props = {
  icon?: React.ReactNode;
  title: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
};

/** Consistent empty state for lists, results and not-yet-populated panels. */
export function EmptyState({
  icon,
  title,
  description,
  action,
  className,
}: Props) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-lg border border-dashed border-border px-6 py-10 text-center",
        className
      )}
    >
      {icon && (
        <div className="mb-3 text-muted-foreground" aria-hidden="true">
          {icon}
        </div>
      )}

      <p className="text-body font-medium text-foreground">{title}</p>

      {description && (
        <p className="mt-1 max-w-md text-label text-muted-foreground">
          {description}
        </p>
      )}

      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}