"use client";

import { useRouter } from "next/navigation";
import { Building2 } from "lucide-react";

import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { TickerLookupForm } from "@/components/ui/ticker-lookup";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/card";

export default function CompanyPage() {
  const router = useRouter();

  return (
    <div className="mx-auto max-w-7xl space-y-8">
      <PageHeader
        eyebrow="Company"
        title="Companies"
        description="Browse and analyze public companies."
      />

      <Card>
        <CardHeader>
          <CardTitle as="h2">Look up a company</CardTitle>
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
        icon={<Building2 size={28} aria-hidden="true" />}
        title="Start with a ticker lookup"
        description="There is no company directory in this workspace yet. Look up a symbol above to view its profile, then run an AI analysis from there."
      />
    </div>
  );
}