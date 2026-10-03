import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  Building2,
  ClipboardList,
  ShieldCheck,
  type LucideIcon,
} from "lucide-react";

const CAPABILITIES: {
  title: string;
  description: string;
  icon: LucideIcon;
}[] = [
  {
    title: "Company profile",
    description:
      "Key business information, products, revenue segments and competitors.",
    icon: Building2,
  },
  {
    title: "Financial analysis",
    description:
      "Financial health, key metrics, profitability, growth and historical performance.",
    icon: ClipboardList,
  },
  {
    title: "Valuation",
    description: "Intrinsic value, DCF, multiples and fair value estimates.",
    icon: BarChart3,
  },
  {
    title: "Risk analysis",
    description: "Key risks, uncertainties and risk score.",
    icon: ShieldCheck,
  },
];

/**
 * "What you can do" — a static statement of what a company lookup unlocks.
 *
 * Informational only: no data fetching, so it renders identically on the server
 * and the client and never delays the ticker form above it.
 */
export function CompanyCapabilities() {
  return (
    <section aria-labelledby="company-capabilities-heading" className="space-y-3">
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2">
        <h2
          id="company-capabilities-heading"
          className="text-title text-foreground"
        >
          What you can do
        </h2>

        <Link
          href="/company/AAPL"
          className="group inline-flex shrink-0 items-center gap-1.5 rounded-sm text-label font-medium text-brand transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          View sample company
          <ArrowRight
            size={14}
            aria-hidden="true"
            className="transition-transform duration-150 group-hover:translate-x-0.5"
          />
        </Link>
      </div>

      <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {CAPABILITIES.map(({ title, description, icon: Icon }) => (
          <li key={title}>
            <article className="flex h-full items-start gap-3 rounded-xl border border-border bg-card p-4 shadow-card transition-[border-color,box-shadow] duration-150 hover:border-border-strong hover:shadow-soft">
              <span
                className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand-subtle text-brand"
                aria-hidden="true"
              >
                <Icon size={17} />
              </span>

              <div className="min-w-0">
                <h3 className="text-label font-semibold text-foreground">
                  {title}
                </h3>
                <p className="mt-1 text-label leading-relaxed text-muted-foreground">
                  {description}
                </p>
              </div>
            </article>
          </li>
        ))}
      </ul>
    </section>
  );
}