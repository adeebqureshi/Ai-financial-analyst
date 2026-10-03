/**
 * Company identity registry and logo resolution.
 *
 * The backend deliberately ships only financial facts — `CompanyData` carries
 * ticker, name, sector, industry, market_cap and description, with no domain
 * and no logo URL. Brand identity is therefore resolved here, on the client,
 * from a single table rather than being duplicated per page.
 *
 * Adding a ticker is a one-line change below and needs no edits anywhere else:
 * `<CompanyLogo>` degrades to a deterministic monogram for unlisted symbols,
 * and the backend's `company.name` always wins over this map when available.
 */

export type CompanyMeta = {
  /** Canonical uppercase symbol, used as the registry key. */
  readonly symbol: string;
  /** Human-readable brand name, used for alt text. */
  readonly name: string;
  /**
   * Primary company domain. Also the logo cache key, so two symbols sharing a
   * domain (GOOGL/GOOG) resolve to the same asset.
   */
  readonly domain: string;
};

const COMPANY_REGISTRY: Record<string, CompanyMeta> = {
  AAPL: { symbol: "AAPL", name: "Apple", domain: "apple.com" },
  MSFT: { symbol: "MSFT", name: "Microsoft", domain: "microsoft.com" },
  NVDA: { symbol: "NVDA", name: "NVIDIA", domain: "nvidia.com" },
  GOOGL: { symbol: "GOOGL", name: "Alphabet", domain: "google.com" },
  GOOG: { symbol: "GOOG", name: "Alphabet", domain: "google.com" },
  AMZN: { symbol: "AMZN", name: "Amazon", domain: "amazon.com" },
  TSLA: { symbol: "TSLA", name: "Tesla", domain: "tesla.com" },
  META: { symbol: "META", name: "Meta Platforms", domain: "meta.com" },
  NFLX: { symbol: "NFLX", name: "Netflix", domain: "netflix.com" },
  AMD: { symbol: "AMD", name: "AMD", domain: "amd.com" },
  INTC: { symbol: "INTC", name: "Intel", domain: "intel.com" },
  JPM: { symbol: "JPM", name: "JPMorgan Chase", domain: "jpmorganchase.com" },
  V: { symbol: "V", name: "Visa", domain: "visa.com" },
  MA: { symbol: "MA", name: "Mastercard", domain: "mastercard.com" },
  WMT: { symbol: "WMT", name: "Walmart", domain: "walmart.com" },
  COST: { symbol: "COST", name: "Costco", domain: "costco.com" },
  CRM: { symbol: "CRM", name: "Salesforce", domain: "salesforce.com" },
  ORCL: { symbol: "ORCL", name: "Oracle", domain: "oracle.com" },
  ADBE: { symbol: "ADBE", name: "Adobe", domain: "adobe.com" },
  AVGO: { symbol: "AVGO", name: "Broadcom", domain: "broadcom.com" },
  KO: { symbol: "KO", name: "Coca-Cola", domain: "coca-colacompany.com" },
  PEP: { symbol: "PEP", name: "PepsiCo", domain: "pepsico.com" },
  DIS: { symbol: "DIS", name: "Disney", domain: "disney.com" },
  BA: { symbol: "BA", name: "Boeing", domain: "boeing.com" },
  XOM: { symbol: "XOM", name: "Exxon Mobil", domain: "exxonmobil.com" },
  PFE: { symbol: "PFE", name: "Pfizer", domain: "pfizer.com" },
  JNJ: { symbol: "JNJ", name: "Johnson & Johnson", domain: "jnj.com" },
  WFC: { symbol: "WFC", name: "Wells Fargo", domain: "wellsfargo.com" },
  GS: { symbol: "GS", name: "Goldman Sachs", domain: "goldmansachs.com" },
  T: { symbol: "T", name: "AT&T", domain: "att.com" },
  CSCO: { symbol: "CSCO", name: "Cisco", domain: "cisco.com" },
  AMAT: { symbol: "AMAT", name: "Applied Materials", domain: "appliedmaterials.com" },
  MU: { symbol: "MU", name: "Micron", domain: "micron.com" },
  SBUX: { symbol: "SBUX", name: "Starbucks", domain: "starbucks.com" },
  NKE: { symbol: "NKE", name: "Nike", domain: "nike.com" },
  MCD: { symbol: "MCD", name: "McDonald's", domain: "mcdonalds.com" },
  HD: { symbol: "HD", name: "Home Depot", domain: "homedepot.com" },
  CAT: { symbol: "CAT", name: "Caterpillar", domain: "caterpillar.com" },
  GE: { symbol: "GE", name: "GE Aerospace", domain: "ge.com" },
  UBER: { symbol: "UBER", name: "Uber", domain: "uber.com" },
  ABNB: { symbol: "ABNB", name: "Airbnb", domain: "airbnb.com" },
  SPOT: { symbol: "SPOT", name: "Spotify", domain: "spotify.com" },
  PYPL: { symbol: "PYPL", name: "PayPal", domain: "paypal.com" },
  SQ: { symbol: "SQ", name: "Block", domain: "block.xyz" },
  SHOP: { symbol: "SHOP", name: "Shopify", domain: "shopify.com" },
  ARM: { symbol: "ARM", name: "Arm Holdings", domain: "arm.com" },
  PLTR: { symbol: "PLTR", name: "Palantir", domain: "palantir.com" },
  COIN: { symbol: "COIN", name: "Coinbase", domain: "coinbase.com" },
  SMCI: { symbol: "SMCI", name: "Super Micro", domain: "supermicro.com" },
  LLY: { symbol: "LLY", name: "Eli Lilly", domain: "lilly.com" },
  UNH: { symbol: "UNH", name: "UnitedHealth", domain: "unitedhealthgroup.com" },
  BRKB: { symbol: "BRKB", name: "Berkshire Hathaway", domain: "berkshirehathaway.com" },
};

/**
 * Normalise casing and punctuation, and strip provider suffixes.
 *
 * These components receive symbols from routes (`/company/brk.b`), chat tool
 * payloads, stored session titles and history rows, so the symbol arrives in
 * several shapes: `aapl`, ` AAPL `, `brk.b`, `BF-B`. Folding them here keeps
 * every call site free of ad-hoc cleaning.
 */
export function normalizeTicker(ticker: string | null | undefined): string {
  if (!ticker) return "";

  return ticker
    .trim()
    .toUpperCase()
    // `.` and `-` are both valid ticker separators (BRK.B, BF-B); fold to `_`.
    .replace(/[.\-\s]/g, "_");
}

/**
 * Registry lookup. Returns `null` for symbols with no known identity, which is
 * the normal, expected outcome for a long-tail ticker — callers must stay
 * prepared to render a monogram.
 */
export function getCompanyMeta(
  ticker: string | null | undefined
): CompanyMeta | null {
  const symbol = normalizeTicker(ticker);

  if (!symbol) return null;

  return COMPANY_REGISTRY[symbol] ?? null;
}

/** Friendly name when known; otherwise the ticker, so text never renders empty. */
export function getCompanyName(
  ticker: string | null | undefined,
  backendName?: string | null
): string {
  const trimmed = backendName?.trim();

  if (trimmed) return trimmed;

  return getCompanyMeta(ticker)?.name ?? normalizeTicker(ticker);
}

/**
 * Up to two characters for the monogram fallback.
 *
 * A single letter is ambiguous at 20px — `A` reads as Adobe, AMD or Amazon — so
 * every symbol contributes two characters where it has them, and true
 * single-letter tickers (`V`, `T`, `F`) simply render one.
 */
export function getMonogram(ticker: string | null | undefined): string {
  const symbol = normalizeTicker(ticker).replace(/_/g, "");

  if (!symbol) return "?";

  return symbol.slice(0, 2);
}

/**
 * Deterministic logo URL for a company domain.
 *
 * Providers are tried in order and the first non-null URL wins; `null` from all
 * of them means "no logo available — use the monogram". Keeping resolution
 * behind this function means swapping or adding a vendor is a one-place edit.
 */
export type LogoProvider = (domain: string, size: number) => string | null;

/**
 * Google favicon service, keyed by domain.
 *
 * Selected after testing the alternatives: `logo.clearbit.com` no longer
 * resolves in DNS (HubSpot sunset it) and `img.logo.dev` returns 401 without an
 * API key, leaving this as the only keyless source that still works. It serves
 * raster PNG rather than SVG, which makes it the weaker long-term choice — see
 * the delivery report, which recommends vendoring SVGs for production.
 */
const googleFaviconProvider: LogoProvider = (domain, size) =>
  `https://www.google.com/s2/favicons?domain=${encodeURIComponent(
    domain
  )}&sz=${Math.max(64, size)}`;

/** Tried in order; each must be deterministic and must not throw. */
const LOGO_PROVIDERS: readonly LogoProvider[] = [googleFaviconProvider];

/** Resolved logo URL, or `null` when the symbol has no registry entry. */
export function getCompanyLogoUrl(
  ticker: string | null | undefined,
  size = 64
): string | null {
  const meta = getCompanyMeta(ticker);

  if (!meta) return null;

  for (const provider of LOGO_PROVIDERS) {
    try {
      const url = provider(meta.domain, size);

      if (url) return url;
    } catch {
      // A misbehaving provider must never propagate: fall through to the next
      // one and ultimately to the monogram, since this runs during render.
    }
  }

  return null;
}
