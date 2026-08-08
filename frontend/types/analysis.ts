export interface AnalyzeRequest {
  company: string;
}

export interface AnalyzeResponse {
  success: boolean;
  message: string;
  data: unknown;
}