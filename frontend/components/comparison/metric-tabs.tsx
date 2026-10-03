"use client";

import {
  Activity,
  HeartPulse,
  LayoutGrid,
  Table2,
  TrendingUp,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/lib/utils";

export type MetricTabId =
  | "key-metrics"
  | "financial-health"
  | "valuation"
  | "comparison-table";

type MetricTab = {
  id: MetricTabId;
  label: string;
  icon: LucideIcon;
};

/**
 * Only views backed by fields the `/compare` response actually returns are
 * exposed. There is no risk or growth series in the comparison payload, so no
 * tab is rendered for them rather than shipping a tab that switches to nothing.
 */
export const METRIC_TABS: MetricTab[] = [
  { id: "key-metrics", label: "Key metrics", icon: LayoutGrid },
  { id: "financial-health", label: "Financial health", icon: HeartPulse },
  { id: "valuation", label: "Valuation", icon: TrendingUp },
  { id: "comparison-table", label: "Comparison table", icon: Table2 },
];

type Props = {
  active: MetricTabId;
  onChange: (tab: MetricTabId) => void;
  className?: string;
};

export function MetricTabs({ active, onChange, className }: Props) {
  return (
    <div
      role="tablist"
      aria-label="Comparison views"
      className={cn(
        "-mx-4 flex snap-x items-center gap-2 overflow-x-auto px-4 pb-1 sm:mx-0 sm:px-0",
        className
      )}
    >
      {METRIC_TABS.map(({ id, label, icon: Icon }) => {
        const selected = id === active;

        return (
          <button
            key={id}
            type="button"
            role="tab"
            id={`comparison-tab-${id}`}
            aria-selected={selected}
            aria-controls={`comparison-panel-${id}`}
            tabIndex={selected ? 0 : -1}
            onClick={() => onChange(id)}
            onKeyDown={(event) => {
              const index = METRIC_TABS.findIndex((tab) => tab.id === active);
              if (event.key === "ArrowRight") {
                event.preventDefault();
                onChange(METRIC_TABS[(index + 1) % METRIC_TABS.length].id);
              }
              if (event.key === "ArrowLeft") {
                event.preventDefault();
                onChange(
                  METRIC_TABS[(index - 1 + METRIC_TABS.length) % METRIC_TABS.length].id
                );
              }
            }}
            className={cn(
              "inline-flex h-10 shrink-0 snap-start items-center gap-2 rounded-xl px-3.5 text-label font-medium transition-colors duration-150",
              "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
              selected
                ? "bg-primary text-primary-foreground shadow-soft"
                : "border border-border bg-card text-foreground hover:border-border-strong hover:bg-muted"
            )}
          >
            <Icon size={16} aria-hidden="true" />
            {label}
          </button>
        );
      })}
    </div>
  );
}

export function MetricTabPanel({
  id,
  children,
}: {
  id: MetricTabId;
  children: React.ReactNode;
}) {
  return (
    <div
      role="tabpanel"
      id={`comparison-panel-${id}`}
      aria-labelledby={`comparison-tab-${id}`}
      tabIndex={0}
      className="min-w-0 overflow-hidden rounded-2xl border border-border bg-card shadow-card focus-visible:outline-none"
    >
      {children}
    </div>
  );
}

export function PanelPlaceholder({
  icon: Icon = Activity,
  title,
  description,
}: {
  icon?: LucideIcon;
  title: string;
  description: string;
}) {
  return (
    <div className="flex flex-col items-center justify-center px-6 py-14 text-center">
      <span
        className="flex size-10 items-center justify-center rounded-xl bg-muted text-muted-foreground"
        aria-hidden="true"
      >
        <Icon size={18} />
      </span>
      <p className="mt-3.5 text-subtitle text-foreground">{title}</p>
      <p className="mt-1.5 max-w-md text-label leading-relaxed text-muted-foreground">
        {description}
      </p>
    </div>
  );
}
