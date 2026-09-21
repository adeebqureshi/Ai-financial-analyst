"use client";

import { Activity, Building2, Landmark } from "lucide-react";

import { Badge, DemoBadge, RecommendationBadge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

type Props = {
  company: {
    name: string;
    ticker: string;
    sector?: string;
    industry?: string;
    description?: string;
  };

  recommendation: string;
};

/** The backend flags synthetic fixtures by suffixing the company name. */
function isDemoData(name: string): boolean {
  return name.includes("[DEMO / SYNTHETIC DATA]");
}

export function CompanyHeader({ company, recommendation }: Props) {
  const isDemo = isDemoData(company.name);
  const displayName = isDemo
    ? company.name.replace(" [DEMO / SYNTHETIC DATA]", "")
    : company.name;

  return (
    <section data-testid="company-header" aria-labelledby="company-heading">
      <Card className="p-6 sm:p-8">
        <div className="flex flex-col gap-8 xl:flex-row xl:items-start xl:justify-between">
          <div className="min-w-0 max-w-3xl">
            <div className="flex flex-wrap items-center gap-2">
              <Badge variant="brand">
                <Activity size={13} aria-hidden="true" />
                AI Analysis
              </Badge>

              {isDemo && <DemoBadge label="Demo data" />}
            </div>

            <h1
              id="company-heading"
              className="mt-4 text-display break-words text-foreground"
            >
              {displayName}
            </h1>

            <div className="mt-4 flex flex-wrap items-center gap-2">
              <Badge variant="outline" className="font-mono">
                {company.ticker}
              </Badge>

              {company.sector && (
                <Badge variant="neutral">
                  <Landmark size={13} aria-hidden="true" />
                  {company.sector}
                </Badge>
              )}

              {company.industry && (
                <Badge variant="neutral">
                  <Building2 size={13} aria-hidden="true" />
                  {company.industry}
                </Badge>
              )}
            </div>

            {company.description && (
              <p className="mt-5 text-body text-muted-foreground">
                {company.description}
              </p>
            )}

            {isDemo && (
              <p className="mt-2 text-caption text-warning">
                All values shown for this company come from the backend&apos;s
                synthetic demo fixtures, not from live market data.
              </p>
            )}
          </div>

          <div className="w-full shrink-0 rounded-lg border border-border bg-background p-5 sm:max-w-72">
            <p className="text-caption font-medium uppercase tracking-wide text-subtle-foreground">
              Backend recommendation
            </p>

            <div className="mt-3">
              <RecommendationBadge
                recommendation={recommendation}
                className="px-3 py-1 text-body"
              />
            </div>
          </div>
        </div>
      </Card>
    </section>
  );
}