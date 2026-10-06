/**
 * Single shared company resolver + search.
 */
import { COMPANIES, type CompanyInfo } from "./companies-data";

export type { CompanyInfo };

const SUFFIX = new RegExp(
  String.raw`\b(inc|incorporated|corp|corporation|company|co|ltd|limited|plc|holdings?|group|technologies?|technology|platforms?|systems?|labs|laboratories|pharmaceuticals?)\b\.?,?`,
  "i",
);

export function normalizeCompanyQuery(value: string | null | undefined): string {
  if (typeof value !== "string") return "";
  return value.replace(/\s+/g, " ").trim();
}

function stripNoise(value: string): string {
  const lowered = value.trim().toLowerCase().replace(/&/g, " and ");
  const noPunct = lowered.replace(/[^a-z0-9\s]/g, " ");
  return noPunct.replace(SUFFIX, " ").replace(/\s+/g, " ").trim();
}

function splitWords(value: string): string[] {
  return value.split(/[^a-z0-9]+/).filter(Boolean);
}

type Score = [number, number];

function scoreCompany(company: CompanyInfo, raw: string, norm: string): Score | null {
  const trimmed = raw.trim();
  if (!trimmed) return null;
  const upper = trimmed.toUpperCase();
  const rawLow = trimmed.toLowerCase();
  const tickerLow = company.ticker.toLowerCase();
  const nameLow = company.name.toLowerCase();
  const nameNorm = stripNoise(company.name);
  const aliasNorms = (company.aliases ?? []).map(stripNoise);

  if (upper === company.ticker) return [0, 0];
  if (tickerLow.startsWith(rawLow)) return [1, 0];
  if (norm && (norm === nameNorm || aliasNorms.includes(norm))) return [2, 0];
  if (norm) {
    const words = [...splitWords(nameLow)];
    for (const a of company.aliases ?? []) words.push(...splitWords(a.toLowerCase()));
    if (words.some((w) => w.startsWith(norm))) return [3, 0];
    if (nameNorm.startsWith(norm)) return [4, 0];
    if (aliasNorms.some((a) => a.startsWith(norm))) return [5, 0];
    if (tickerLow.includes(rawLow)) return [6, 0];
    if (nameNorm.includes(norm) || aliasNorms.some((a) => a.includes(norm))) {
      const pos = nameNorm.indexOf(norm);
      return [7, pos >= 0 ? pos : 999];
    }
  }
  return null;
}

export function searchCompanies(query: string | null | undefined, limit = 8): CompanyInfo[] {
  const q = normalizeCompanyQuery(query);
  if (!q) return [];
  const norm = stripNoise(q);
  if (!norm) return [];
  const scored: Array<{ score: Score; company: CompanyInfo }> = [];
  for (const company of COMPANIES) {
    const score = scoreCompany(company, q, norm);
    if (score) scored.push({ score, company });
  }
  scored.sort((a, b) => a.score[0] - b.score[0] || a.score[1] - b.score[1] || (a.company.ticker < b.company.ticker ? -1 : 1));
  const seen = new Set<string>();
  const out: CompanyInfo[] = [];
  for (const { company } of scored) {
    if (seen.has(company.ticker)) continue;
    seen.add(company.ticker);
    out.push(company);
    if (out.length >= Math.max(1, limit)) break;
  }
  return out;
}

/**
 * resolveCompany("apple") -> { ticker: "AAPL", name: "Apple Inc." }
 * resolveCompany("aapl")  -> { ticker: "AAPL", name: "Apple Inc." }
 * Returns null when nothing matches; never throws, never fabricates.
 */
export function resolveCompany(value: string | null | undefined): CompanyInfo | null {
  const q = normalizeCompanyQuery(value);
  if (!q) return null;
  const norm = stripNoise(q);
  const upper = q.toUpperCase();
  const byTicker = COMPANIES.find((c) => c.ticker === upper);
  if (byTicker) return byTicker;
  for (const company of COMPANIES) {
    const aliasNorms = (company.aliases ?? []).map(stripNoise);
    if (norm && (norm === stripNoise(company.name) || aliasNorms.includes(norm))) return company;
  }
  if (norm && norm.length <= 6) {
    const folded = COMPANIES.find((c) => c.ticker.toLowerCase() === norm);
    if (folded) return folded;
  }
  const [top] = searchCompanies(q, 1);
  if (top) {
    const score = scoreCompany(top, q, norm);
    if (score && score[0] <= 5) return top;
  }
  return null;
}

export function isResolvableCompany(value: string | null | undefined): boolean {
  return resolveCompany(value) !== null;
}
