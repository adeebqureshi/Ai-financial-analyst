import Link from "next/link";
import {
  ArrowRight,
  BarChart3,
  ClipboardList,
  ShieldCheck,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

const DELIVERABLES: {
  title: string;
  description: string;
  icon: LucideIcon;
}[] = [
  {
    title: "Valuation",
    description: "Intrinsic value, DCF, multiples and valuation insights.",
    icon: BarChart3,
  },
  {
    title: "Financial health",
    description: "Key metrics, profitability, liquidity and growth.",
    icon: ClipboardList,
  },
  {
    title: "Risk analysis",
    description: "Key risks, uncertainties and risk score.",
    icon: ShieldCheck,
  },
  {
    title: "AI copilot",
    description: "Ask follow-up questions and get grounded answers.",
    icon: Sparkles,
  },
];

/**
 * "What you'll get" — a static statement of the pipeline's deliverables.
 *
 * Informational only: no data fetching, so it renders identically on the server
 * and the client and never delays the ticker form above it.
 */
export function AnalysisDeliverables() {
  return (
    <section aria-labelledby="analysis-deliverables-heading" className="space-y-3">
      <div className="flex flex-wrap items-end justify-between gap-x-6 gap-y-2">
        <h2
          id="analysis-deliverables-heading"
          className="text-title text-foreground"
        >
          What you&apos;ll get
        </h2>

        <Link
          href="/analysis/AAPL"
          className="group inline-flex shrink-0 items-center gap-1.5 rounded-sm text-label font-medium text-brand transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
        >
          View sample analysis
          <ArrowRight
            size={14}
            aria-hidden="true"
            className="transition-transform duration-150 group-hover:translate-x-0.5"
          />
        </Link>
      </div>

      <ul className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {DELIVERABLES.map(({ title, description, icon: Icon }) => (
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