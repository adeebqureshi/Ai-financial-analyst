export interface CompanyData {
  ticker: string;
  name: string;
  sector: string | null;
  industry: string | null;
  market_cap: number | null;
  description: string | null;
}

export interface ValuationResultData {
  intrinsic_value: number;
  upside: number;
  recommendation: string;
  current_price: number;
  discount_rate: number;
}

export interface HealthScoreData {
  score: number;
  rating: string;
  piotroski_score: number;
  altman_score: number;
  beneish_score: number;
}

export interface MarketData {
  ticker: string;
  exchange: string | null;
  current_price: number | null;
  currency: string;
  market_cap: number | null;
  volume: number | null;
  beta: number | null;
  pe_ratio: number | null;
  eps: number | null;
  dividend_yield: number | null;
  week_52_high: number | null;
  week_52_low: number | null;
  price_available?: boolean;
  provider?: string | null;
  as_of?: string | null;
  cached?: boolean;
  stale?: boolean;
}

export interface StatementData {
  revenue: number;
  operating_income: number;
  net_income: number;
  total_assets: number;
  total_liabilities: number;
  cash: number;
  debt: number;
  shares_outstanding: number;
  free_cash_flow: number;
}

export interface AnalyzeData {
  ticker: string;
  query: string;
  company: CompanyData;
  market: MarketData;
  statement: StatementData;
  valuation: ValuationResultData;
  health: HealthScoreData;
  recommendation: string;
}

export interface SearchHitData {
  id: string;
  text: string;
  score: number;
  ticker: string | null;
  filing_type: string | null;
  filing_date: string | null;
  section: string | null;
  source: string | null;
  document_id: string | null;
  filename: string | null;
  page: number | null;
  chunk_id: string | null;
}

export interface SearchResultData {
  query: string;
  hits: SearchHitData[];
  total: number;
  retrieval_time_ms: number;
}

export interface RiskAssessmentData {
  health_score: number;
  health_rating: string;
  piotroski: Record<string, unknown>;
  altman: Record<string, unknown>;
  beneish: Record<string, unknown>;
  risk_level: string;
}

export interface CompareItemData {
  ticker: string;
  name: string | null;
  intrinsic_value: number;
  upside: number;
  recommendation: string;
  health_score: number | null;
}

export interface CompareData {
  results: CompareItemData[];
  best: string;
}

export interface ReportData {
  ticker: string;
  title: string;
  content: string;
  format: string;
}

export interface AgentToolExecution {
  tool: string;
  status: "done" | "running" | "error" | "skipped";
  detail?: string;
}

export interface DocumentCitation {
  document_id: string;
  filename: string;
  page: number | null;
  chunk_id: string | null;
  score: number | null;
}

export interface DocumentData {
  document_id: string;
  filename: string;
  pages: number;
  chunks: number;
  status: string;
  created_at: string | null;
}

export interface DocumentListData {
  documents: DocumentData[];
  total: number;
}

export interface ErrorDetail {
  field: string | null;
  message: string;
  code: string | null;
}

export interface ResponseMetadata {
  timestamp: string;
  request_id: string | null;
  pagination: unknown;
}

export interface ApiResponse<T> {
  success: boolean;
  message: string;
  data: T | null;
  errors: ErrorDetail[] | null;
  metadata: ResponseMetadata;
}
