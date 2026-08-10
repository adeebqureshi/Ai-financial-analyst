import { api } from "./api";

export async function getFinancialStatements(
  ticker: string
) {
  const company = await api.company(ticker);

  const valuation = await api.valuation({
    ticker,
  });

  const ratios =
    await api.financialRatios({
      ticker,
    });

  const risk =
    await api.riskAnalysis({
      ticker,
    });

  return {
    company,
    valuation,
    ratios,
    risk,
  };
}