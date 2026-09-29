"use client";

import Link from "next/link";
import {
  ArrowUpRight,
  BookOpenText,
  Building2,
  Crosshair,
  FileText,
  GitCompare,
  SlidersHorizontal,
  type LucideIcon,
} from "lucide-react";

import { SectionHeading } from "@/components/ui/page-header";

type Action = {
  title: string;
  description: string;
  href: string;
  icon: LucideIcon;
  primary?: boolean;
};

const actions: Action[] = [
  {
    title: "Analyze company",
    description: "Full AI pipeline for a ticker",
    href: "/analysis",
    icon: Crosshair,
    primary: true,
  },
  {
    title: "Company profile",
    description: "Sector context and company details",
    href: "/company",
    icon: Building2,
    primary: true,
  },
  {
    title: "Compare companies",
    description: "Side-by-side metrics",
    href: "/compare",
    icon: GitCompare,
    primary: true,
  },
  {
    title: "Financial documents",
    description: "Upload filings, ask questions",
    href: "/research",
    icon: BookOpenText,
  },
  {
    title: "Generate report",
    description: "LLM research write-up",
    href: "/reports",
    icon: FileText,
  },
];

export function QuickActions() {
  return (
    <section aria-labelledby="quick-actions-heading" className="space-y-4">
      <SectionHeading
        id="quick-actions-heading"
        title="Quick actions"
        description="The research workflows this workspace exposes."
      />

      <div className="grid gap-x-8 gap-y-1 sm:grid-cols-2 sm:gap-x-10">
        {actions.map((action) => {
          const Icon = action.icon;

          return (
            <Link
              key={action.title}
              href={action.href}
              className="group -mx-2 flex items-center gap-3 rounded-lg px-2 py-2.5 transition-colors hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              <span
                className={
                  action.primary
                    ? "flex size-8 shrink-0 items-center justify-center rounded-lg bg-brand-subtle text-brand"
                    : "flex size-8 shrink-0 items-center justify-center rounded-lg text-muted-foreground transition-colors group-hover:text-foreground"
                }
              >
                <Icon size={16} aria-hidden="true" />
              </span>

              <span className="min-w-0 flex-1">
                <span className="block text-label font-medium text-foreground">
                  {action.title}
                </span>
                <span className="mt-0.5 block truncate text-caption text-muted-foreground">
                  {action.description}
                </span>
              </span>

              <ArrowUpRight
                size={14}
                className="shrink-0 text-subtle-foreground transition-all duration-150 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-brand"
                aria-hidden="true"
              />
            </Link>
          );
        })}
      </div>
    </section>
  );
}
