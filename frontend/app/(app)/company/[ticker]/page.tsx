import { redirect } from "next/navigation";

/**
 * `/company/[ticker]` is retired in favour of `/analysis/[ticker]`.
 *
 * The symbol is the route segment the user (or an old link) already supplied,
 * so nothing is invented: it is normalised and handed to the canonical route,
 * which owns validation and error handling for unknown tickers.
 */
export default async function CompanyDetailPage({
  params,
}: {
  params: Promise<{ ticker: string }>;
}) {
  const { ticker } = await params;
  const symbol = ticker.trim().toUpperCase();

  redirect(`/analysis/${encodeURIComponent(symbol)}`);
}