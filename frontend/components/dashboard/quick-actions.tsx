"use client";

import Link from "next/link";
import {
  ArrowRight,
  BookOpenText,
  Crosshair,
  FileText,
  GitCompare,
  Search,
  type LucideIcon,
} from "lucide-react";

import { SectionHeading } from "@/components/ui/page-header";

type Action = {
  title: string;
  description: string;
  href: string;
  icon: LucideIcon;
};

/**
 * The Command Hub's primary navigation. Every entry points at an existing,
 * already-working route — this is a launcher, not a second implementation of
 * any workflow.
 */
const actions: Action[] = [
  {
    title: "Analyze company",
    description: "Run financial, valuation, health and risk analysis.",
    href: "/analysis",
    icon: Crosshair,
  },
  {
    title: "Compare companies",
    description:
      "Compare companies across valuation, financial health and market metrics.",
    href: "/compare",
    icon: GitCompare,
  },
  {
    title: "Research",
    description: "Search financial information, filings and knowledge.",
    href: "/research",
    icon: BookOpenText,
  },
  {
    title: "Search",
    description: "Query documents and filings with hybrid retrieval.",
    href: "/search",
    icon: Search,
  },
  {
    title: "Reports",
    description: "Generate and review AI-powered financial reports.",
    href: "/reports",
    icon: FileText,
  },
];

export function QuickActions() {
  return (
    <section aria-labelledby="quick-actions-heading" className="space-y-4">
      <SectionHeading
        id="quick-actions-heading"
        title="What do you want to do?"
        description="Start any workflow in this workspace."
      />

      <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
        {actions.map((action) => {
          const Icon = action.icon;

          return (
            <li key={action.title}>
              <Link
                href={action.href}
                className="group flex h-full flex-col gap-3 rounded-xl border border-border bg-card p-4 transition-colors duration-150 hover:border-border-strong hover:bg-surface focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
              >
                <span className="flex size-9 items-center justify-center rounded-lg bg-brand-subtle text-brand">
                  <Icon size={17} aria-hidden="true" />
                </span>

                <span className="flex-1">
                  <span className="block text-label font-semibold text-foreground">
                    {action.title}
                  </span>
                  <span className="mt-1 block text-caption leading-relaxed text-muted-foreground">
                    {action.description}
                  </span>
                </span>

                <span
                  className="flex items-center gap-1 text-caption font-medium text-brand opacity-0 transition-opacity duration-150 group-hover:opacity-100 group-focus-visible:opacity-100"
                  aria-hidden="true"
                >
                  Open
                  <ArrowRight
                    size={13}
                    className="transition-transform duration-150 group-hover:translate-x-0.5"
                  />
                </span>
              </Link>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
