"use client";

import Link from "next/link";
import { BookOpenText, CircleDot, Database, ServerCog } from "lucide-react";

import { useWorkspaceStatus } from "@/hooks/use-workspace-status";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

type Cell = {
  label: string;
  value: string;
  hint?: string;
  tone: "gain" | "loss" | "warning" | "muted";
  icon: typeof CircleDot;
};

const toneDot: Record<Cell["tone"], string> = {
  gain: "bg-gain",
  loss: "bg-loss",
  warning: "bg-warning",
  muted: "bg-subtle-foreground",
};

export function StatusStrip() {
  const status = useWorkspaceStatus();

  const cells: Cell[] = [
    {
      label: "Backend",
      value:
        status.status === "checking"
          ? "Checking…"
          : status.status === "healthy"
            ? "Operational"
            : status.status === "degraded"
              ? "Degraded"
              : "Unavailable",
      hint: status.detail,
      tone:
        status.status === "healthy"
          ? "gain"
          : status.status === "degraded"
            ? "warning"
            : status.status === "checking"
              ? "muted"
              : "loss",
      icon: ServerCog,
    },
    {
      label: "Environment",
      value: status.demoMode ? "Demo mode" : "Live data",
      hint: status.version ? `API v${status.version}` : "Version unavailable",
      tone: status.demoMode ? "warning" : "muted",
      icon: CircleDot,
    },
    {
      label: "Knowledge base",
      value: status.documentsPending
        ? "Indexing…"
        : status.documentCount === null
          ? "Unavailable"
          : `${status.documentCount} document${status.documentCount === 1 ? "" : "s"}`,
      hint:
        status.documentCount === null && !status.documentsPending
          ? "Document service did not respond"
          : "Indexed for retrieval",
      tone: status.documentCount === null ? "loss" : "muted",
      icon: Database,
    },
  ];

  return (
    <section
      aria-label="Workspace status"
      className="grid gap-px overflow-hidden rounded-xl border border-border bg-border sm:grid-cols-2 xl:grid-cols-4"
    >
      {cells.map((cell) => {
        const Icon = cell.icon;

        return (
          <div
            key={cell.label}
            className="flex items-center gap-3 bg-card px-4 py-3.5"
          >
            <Icon
              size={15}
              className="shrink-0 text-subtle-foreground"
              aria-hidden="true"
            />

            <div className="min-w-0 flex-1">
              <p className="text-[11px] font-semibold uppercase tracking-[0.12em] text-subtle-foreground">
                {cell.label}
              </p>

              {status.status === "checking" &&
              cell.label === "Backend" &&
              status.documentsPending ? (
                <Skeleton className="mt-1.5 h-3.5 w-24" />
              ) : (
                <p
                  className={cn(
                    "mt-0.5 flex items-center gap-1.5 truncate text-label font-medium",
                    cell.tone === "gain"
                      ? "text-gain"
                      : cell.tone === "loss"
                        ? "text-loss"
                        : cell.tone === "warning"
                          ? "text-warning"
                          : "text-foreground"
                  )}
                >
                  <span
                    className={cn(
                      "size-1.5 shrink-0 rounded-full",
                      toneDot[cell.tone]
                    )}
                    aria-hidden="true"
                  />
                  {cell.value}
                </p>
              )}

              {cell.hint && (
                <p className="mt-0.5 truncate text-caption text-muted-foreground">
                  {cell.hint}
                </p>
              )}
            </div>
          </div>
        );
      })}

      <Link
        href="/research"
        className="flex items-center gap-3 bg-card px-4 py-3.5 transition-colors hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-ring"
      >
        <BookOpenText
          size={15}
          className="shrink-0 text-brand"
          aria-hidden="true"
        />
        <span className="min-w-0">
          <span className="block text-[11px] font-semibold uppercase tracking-[0.12em] text-subtle-foreground">
            Research
          </span>
          <span className="mt-0.5 block truncate text-label font-medium text-foreground">
            Manage documents
          </span>
        </span>
      </Link>
    </section>
  );
}
