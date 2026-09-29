"use client";

import { useRouter } from "next/navigation";
import { Building2, Sparkles } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { TickerLookupForm } from "@/components/ui/ticker-lookup";
import { TextAction } from "@/components/ui/button";
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
          <TextAction
            href="/analysis"
            icon={<Sparkles size={14} aria-hidden="true" />}
            arrow
          >
            Go to analysis
          </TextAction>
        }
      />
    </div>
  );
}
