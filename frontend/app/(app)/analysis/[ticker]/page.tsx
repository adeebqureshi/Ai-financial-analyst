import { AnalysisView } from "@/components/analysis/analysis-view";

export const dynamic = "force-dynamic";

type Props = {
  params: Promise<{
    ticker: string;
  }>;
};

export default async function AnalysisTickerPage({
  params,
}: Props) {
  const { ticker } = await params;
  const symbol = ticker.toUpperCase();

  return (
    <div className="mx-auto max-w-7xl">
      <AnalysisView ticker={symbol} />
    </div>
  );
}
