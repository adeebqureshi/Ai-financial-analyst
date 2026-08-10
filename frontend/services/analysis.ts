import { api } from "./api";
import type {
  AnalyzeData,
  ApiResponse,
  FinancialStatementInput,
  ValuationParams,
} from "@/types/analysis";

export interface AnalyzeFullRequest {
  ticker: string;
  query: string;
  statement: FinancialStatementInput;
  valuation: ValuationParams;
  piotroski_score: number;
  altman_score: number;
  beneish_score: number;
}

export function analyze(
  payload: AnalyzeFullRequest
): Promise<ApiResponse<AnalyzeData>> {
  return api.analyze(payload.ticker);
}
