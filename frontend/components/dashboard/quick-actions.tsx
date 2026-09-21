"use client";

import Link from "next/link";
import {
  ArrowRight,
  BookOpenText,
  Crosshair,
  FileText,
  GitCompare,
  Search,
  SlidersHorizontal,
  type LucideIcon,
} from "lucide-react";

import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";

type Action = {
  title: string;
  description: string;
  href: string;
  icon: LucideIcon;
};

/**
 * Destinations that exist in the application. Descriptions state what the
 * destination actually does — no workflow is advertised that the app cannot
 * perform (e.g. there is no PDF export and no portfolio tracker).
 */
const actions: Action[] = [
  {
    title: "Analyze a company",
    description: "Run the AI pipeline for one ticker",
    href: "/analysis",
    icon: Crosshair,
  },
  {
    title: "Compare companies",
    description: "Side-by-side valuation and health",
    href: "/compare",
    icon: GitCompare,
  },
  {
    title: "Criteria check",
    description: "Screen one candidate against your criteria",
    href: "/screener",
    icon: SlidersHorizontal,
  },
  {
    title: "Generate a report",
    description: "LLM research report for a company",
    href: "/reports",
    icon: FileText,
  },
  {
    title: "Documents",
    description: "Upload filings and ask grounded questions",
    href: "/research",
    icon: BookOpenText,
  },
  {
    title: "Search knowledge base",
    description: "Hybrid vector + keyword retrieval",
    href: "/search",
    icon: Search,
  },
];

export function QuickActions() {
  return (
    <Card aria-labelledby="quick-actions-heading">
      <CardHeader>
        <div>
          <CardTitle as="h2" id="quick-actions-heading">
            Quick actions
          </CardTitle>
          <p className="mt-1 text-label text-muted-foreground">
            Launch common research workflows
          </p>
        </div>
      </CardHeader>

      <CardBody>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {actions.map((action) => {
            const Icon = action.icon;

            return (
              <Link
                key={action.href}
                href={action.href}
                className="group flex items-start justify-between gap-3 rounded-lg border border-border bg-background p-4 transition-colors hover:border-border-strong hover:bg-muted/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <span className="flex min-w-0 items-start gap-3">
                  <span className="flex size-9 shrink-0 items-center justify-center rounded-md bg-brand-subtle text-brand">
                    <Icon size={17} aria-hidden="true" />
                  </span>

                  <span className="min-w-0">
                    <span className="block text-label font-medium text-foreground">
                      {action.title}
                    </span>
                    <span className="mt-0.5 block text-caption text-muted-foreground">
                      {action.description}
                    </span>
                  </span>
                </span>

                <ArrowRight
                  className="mt-1 size-4 shrink-0 text-muted-foreground transition group-hover:translate-x-0.5 group-hover:text-foreground"
                  aria-hidden="true"
                />
              </Link>
            );
          })}
        </div>
      </CardBody>
    </Card>
  );
}
