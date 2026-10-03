import Link from "next/link";
import { notFound } from "next/navigation";
import { Landmark, Sparkles } from "lucide-react";

import { CompanyLogo } from "@/components/company/company-logo";
import { CompanyLoadError } from "@/components/company/company-load-error";

import { api, ApiError } from "@/services/api";
import { Badge, TickerBadge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody } from "@/components/ui/card";
import { StatBlock } from "@/components/ui/metric";
import { SectionHeading } from "@/components/ui/page-header";

export const dynamic = "force-dynamic";

function formatMarketCap(value: number | null): string {
  if (value === null || Number.isNaN(value)) return "—";

  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    notation: "compact",
    maximumFractionDigits: 2,
  }).format(value);
}

export default async function CompanyDetailPage({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker } = await params;

  const symbol = ticker.toUpperCase();

  let company;

  try {
    const response = await api.analyze(symbol);

    const profile = response?.data?.company;

    if (!profile) {
      // A 2xx response that carries no company profile really is "no such
      // company". Raising it as a 404 ApiError lets the branch below route it
      // to `notFound()` instead of the generic error state.
      throw new ApiError(
        `No company profile was returned for ${symbol}.`,
        404,
        "/analyze"
      );
    }

    company = profile;
  } catch (error) {
    // Only a genuine "this resource does not exist" is a 404. Everything else —
    // an upstream provider failure (5xx), an invalid symbol (422), a backend
    // that is down or unreachable (0/504) — previously fell into the same
    // branch and rendered "This page could not be found", which told users the
    // company does not exist when the real problem was an outage.
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }

    return <CompanyLoadError ticker={symbol} error={error} />;
  }

  return (
    <div className="mx-auto max-w-6xl space-y-10 pb-8">
      <header className="flex flex-col gap-6 border-b border-border pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex min-w-0 items-start gap-5">
          {/* Real brand mark in place of the generic Building2 tile; falls back
              to a monogram for tickers with no registry entry. Decorative — the
              company name and symbol are rendered right beside it. */}
          <CompanyLogo
            ticker={company.ticker}
            companyName={company.name}
            size="lg"
            decorative
          />

          <div className="min-w-0">
            <p className="text-caption font-semibold uppercase tracking-[0.14em] text-brand">
              Company profile
            </p>

            <h1 className="mt-2 text-balance text-display text-foreground">
              {company.name}
            </h1>

            <div className="mt-3.5 flex flex-wrap items-center gap-2">
              <TickerBadge symbol={company.ticker} className="px-2 py-1 text-body" />

              {company.sector && (
                <Badge variant="neutral">
                  <Landmark size={13} aria-hidden="true" />
                  {company.sector}
                </Badge>
              )}

              {company.industry && (
                <Badge variant="outline">{company.industry}</Badge>
              )}
            </div>
          </div>
        </div>

        <Button asChild size="md" className="shrink-0">
          <Link href={`/analysis/${company.ticker}`}>
            <Sparkles size={15} aria-hidden="true" />
            Run AI analysis
          </Link>
        </Button>
      </header>

      <Card>
        <CardBody>
          <dl className="grid gap-x-8 gap-y-6 sm:grid-cols-2 xl:grid-cols-4">
            <StatBlock label="Ticker" value={company.ticker} />
            <StatBlock label="Sector" value={company.sector ?? "—"} />
            <StatBlock label="Industry" value={company.industry ?? "—"} />
            <StatBlock
              label="Market cap"
              value={formatMarketCap(company.market_cap)}
            />
          </dl>
        </CardBody>
      </Card>

      {company.description ? (
        <section aria-labelledby="profile-heading" className="space-y-4">
          <SectionHeading
            id="profile-heading"
            title="About"
            description="Company profile returned by the backend."
          />
          <p className="max-w-3xl text-body leading-relaxed text-muted-foreground">
            {company.description}
          </p>
        </section>
      ) : (
        <section className="space-y-4">
          <SectionHeading title="About" />
          <p className="text-body text-muted-foreground">
            The backend did not return a description for this company.
          </p>
        </section>
      )}
    </div>
  );
}
