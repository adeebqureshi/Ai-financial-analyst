import { api } from "./api";
import {
  AnalyzeRequest,
  AnalyzeResponse,
} from "@/types/analysis";

export function analyze(
  payload: AnalyzeRequest
) {
  return api<AnalyzeResponse>(
    "/analyze",
    {
      method: "POST",
      body: JSON.stringify(payload),
    }
  );
}