import {
  BarChart3,
  ClipboardList,
  ShieldCheck,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

const CAPABILITIES: {
  title: string;
  detail: string;
  icon: LucideIcon;
}[] = [
  { title: "Valuation", detail: "Intrinsic value & DCF", icon: BarChart3 },
  {
    title: "Financial health",
    detail: "Key financial metrics",
    icon: ClipboardList,
  },
  { title: "Risk", detail: "Risk factors & score", icon: ShieldCheck },
  { title: "AI copilot", detail: "Ask grounded questions", icon: Sparkles },
];

/**
 * What an analysis returns, in one line each.
 *
 * This replaced four prose cards under a "What you'll get" heading. The old
 * copy restated the page subtitle at greater length; the useful part was the
 * list of capabilities, so only that survives.
 */
export function AnalysisCapabilities() {
  return (
    <section aria-labelledby="analysis-capabilities-heading">
      <h2 id="analysis-capabilities-heading" className="sr-only">
        What an analysis includes
      </h2>

      <ul className="grid grid-cols-2 gap-x-6 gap-y-4 sm:grid-cols-4">
        {CAPABILITIES.map(({ title, detail, icon: Icon }) => (
          <li key={title} className="flex items-start gap-2.5">
            <Icon
              size={16}
              className="mt-0.5 shrink-0 text-brand"
              aria-hidden="true"
            />

            <div className="min-w-0">
              <p className="text-label font-semibold text-foreground">
                {title}
              </p>
              <p className="text-caption text-muted-foreground">{detail}</p>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}