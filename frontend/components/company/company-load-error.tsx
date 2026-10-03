import { AlertTriangle, WifiOff, SearchX, RefreshCw } from "lucide-react";
import Link from "next/link";

import { ApiError } from "@/services/api";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";

/**
 * Failure state for `/company/[ticker]`.
 *
 * This page resolves the company profile on the server, so it used to collapse
 * every failure into `notFound()`. That made a backend outage, an upstream
 * provider error and an unreachable host all render the generic "404 — This
 * page could not be found", which is actively misleading: users concluded the
 * company did not exist, and support could not tell an outage from a bad
 * ticker.
 *
 * The backend is explicit about these cases and they deserve distinct wording:
 *
 * - `404` — the ticker genuinely does not exist. The page handles that with
 *   `notFound()` and never renders this component.
 * - `422` — the symbol is not a valid ticker (too long, illegal characters).
 *   Retrying will not help; correcting the symbol will.
 * - `5xx` — the market-data provider failed or has no data for this symbol.
 *   The ticker may be real, so the user is told so and offered a retry.
 * - status `0` / `504` — the backend could not be reached or timed out.
 *
 * Retry is a link to the same URL rather than a button with an `onClick`
 * handler: this is a Server Component, and functions cannot be passed to Client
 * Components across the boundary. A plain link also gives the user a shareable
 * URL to retry from.
 */
export function CompanyLoadError({ ticker, error }: { ticker: string; error: unknown }) {
  const apiError = error instanceof ApiError ? error : null;
  const status = apiError?.status;

  let icon = <AlertTriangle />;
  let title = "Could not load this company";
  let description =
    "The company profile could not be retrieved right now. Please try again in a moment.";

  if (status === 422) {
    icon = <SearchX />;
    title = `"${ticker}" is not a valid ticker`;
    description =
      "Ticker symbols are 1–5 letters. Check the symbol and search again.";
  } else if (status === 404) {
    icon = <SearchX />;
    title = `No company found for "${ticker}"`;
    description =
      "Check the symbol, or search for the company from the Companies page.";
  } else if (status === 0 || status === 504) {
    icon = <WifiOff />;
    title = "Cannot reach the analysis service";
    description =
      "The financial data service did not respond. This is a temporary connection problem, not a problem with the ticker.";
  } else if (status !== undefined && status >= 500) {
    icon = <AlertTriangle />;
    title = "Market data is unavailable for this ticker";
    description = apiError?.message
      ? `The upstream data provider could not supply data for "${ticker}": ${apiError.message}`
      : `The upstream data provider could not supply data for "${ticker}". The symbol may be delisted or not covered by the provider.`;
  } else if (apiError?.message) {
    description = apiError.message;
  }

  return (
    <div className="mx-auto max-w-6xl space-y-8 pb-8">
      <EmptyState
        icon={icon}
        tone="neutral"
        title={title}
        description={description}
        action={
          <div className="flex flex-wrap items-center justify-center gap-2">
            <Button asChild variant="secondary" size="md">
              <Link href={`/company/${ticker}`}>
                <RefreshCw size={15} aria-hidden="true" />
                Try again
              </Link>
            </Button>

            <Button asChild variant="ghost" size="md">
              <Link href="/company">Browse companies</Link>
            </Button>
          </div>
        }
      />
    </div>
  );
}