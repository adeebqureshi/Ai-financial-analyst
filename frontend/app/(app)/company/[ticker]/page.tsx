import Link from "next/link";
import { notFound } from "next/navigation";
import { Building2, Landmark, Sparkles } from "lucide-react";

import { api } from "@/services/api";
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
      throw new Error("Company not found");
    }

    company = profile;
  } catch {
    notFound();
  }

  return (
    <div className="mx-auto max-w-6xl space-y-10 pb-8">
      <header className="flex flex-col gap-6 border-b border-border pb-8 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex min-w-0 items-start gap-5">
          <span
            className="flex size-14 shrink-0 items-center justify-center rounded-xl bg-brand-subtle text-brand"
            aria-hidden="true"
          >
            <Building2 size={24} />
          </span>

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
