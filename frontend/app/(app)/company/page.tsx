"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Building2, Sparkles } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { TickerLookupForm } from "@/components/ui/ticker-lookup";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";

export default function CompanyPage() {
  const router = useRouter();

  return (
    <div className="mx-auto max-w-4xl space-y-8 pb-8">
      <PageHeader
        eyebrow="Company & Valuation"
        title="Companies"
        description="Look up a public company, review its profile, then run the full AI analysis."
      />

      <Card>
        <CardHeader>
          <div>
            <CardTitle as="h2">Look up a company</CardTitle>
            <p className="mt-1 text-label text-muted-foreground">
              Enter a ticker symbol to open its profile.
            </p>
          </div>
        </CardHeader>

        <CardBody>
          <TickerLookupForm
            submitLabel="Open profile"
            hint="Enter a ticker to open its company profile."
            onSubmit={(symbol) => router.push(`/company/${symbol}`)}
          />
        </CardBody>
      </Card>

      <EmptyState
        icon={<Building2 size={20} aria-hidden="true" />}
        title="No company directory in this workspace"
        description="Look up a symbol above to view its profile, then run an AI analysis from there."
        action={
          <Link
            href="/analysis"
            className="inline-flex items-center gap-2 rounded-lg border border-border bg-card px-3.5 py-2 text-label font-medium text-foreground shadow-soft transition-colors hover:bg-muted focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
          >
            <Sparkles size={15} aria-hidden="true" />
            Go to analysis
          </Link>
        }
      />
    </div>
  );
}
