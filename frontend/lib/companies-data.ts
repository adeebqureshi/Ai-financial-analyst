/**
 * Canonical company registry + resolver for the whole frontend.
 */
export type CompanyInfo = {
  readonly ticker: string;
  readonly name: string;
  readonly exchange?: string | null;
  readonly aliases?: readonly string[];
};

type Entry = {
  ticker: string;
  name: string;
  exchange?: string;
  aliases?: string[];
};

const ENTRIES: readonly Entry[] = [
  { ticker: "AAPL", name: "Apple Inc.", exchange: "NASDAQ", aliases: ["Apple"] },
  { ticker: "MSFT", name: "Microsoft Corporation", exchange: "NASDAQ", aliases: ["Microsoft"] },
  { ticker: "NVDA", name: "NVIDIA Corporation", exchange: "NASDAQ", aliases: ["NVIDIA", "Nvidia"] },
  { ticker: "GOOGL", name: "Alphabet Inc.", exchange: "NASDAQ", aliases: ["Google", "Alphabet"] },
  { ticker: "GOOG", name: "Alphabet Inc.", exchange: "NASDAQ", aliases: ["Google", "Alphabet"] },
  { ticker: "AMZN", name: "Amazon.com, Inc.", exchange: "NASDAQ", aliases: ["Amazon"] },
  { ticker: "TSLA", name: "Tesla, Inc.", exchange: "NASDAQ", aliases: ["Tesla"] },
  { ticker: "META", name: "Meta Platforms, Inc.", exchange: "NASDAQ", aliases: ["Meta", "Facebook"] },
  { ticker: "NFLX", name: "Netflix, Inc.", exchange: "NASDAQ", aliases: ["Netflix"] },
  { ticker: "AMD", name: "Advanced Micro Devices, Inc.", exchange: "NASDAQ", aliases: ["AMD"] },
  { ticker: "INTC", name: "Intel Corporation", exchange: "NASDAQ", aliases: ["Intel"] },
  { ticker: "CRM", name: "Salesforce, Inc.", exchange: "NYSE", aliases: ["Salesforce"] },
  { ticker: "ORCL", name: "Oracle Corporation", exchange: "NYSE", aliases: ["Oracle"] },
  { ticker: "ADBE", name: "Adobe Inc.", exchange: "NASDAQ", aliases: ["Adobe"] },
  { ticker: "AVGO", name: "Broadcom Inc.", exchange: "NASDAQ", aliases: ["Broadcom"] },
  { ticker: "PLTR", name: "Palantir Technologies Inc.", exchange: "NASDAQ", aliases: ["Palantir"] },
  { ticker: "COIN", name: "Coinbase Global, Inc.", exchange: "NASDAQ", aliases: ["Coinbase"] },
  { ticker: "SHOP", name: "Shopify Inc.", exchange: "NYSE", aliases: ["Shopify"] },
  { ticker: "SQ", name: "Block, Inc.", exchange: "NYSE", aliases: ["Block", "Square"] },
  { ticker: "PYPL", name: "PayPal Holdings, Inc.", exchange: "NASDAQ", aliases: ["PayPal"] },
  { ticker: "SPOT", name: "Spotify Technology S.A.", exchange: "NYSE", aliases: ["Spotify"] },
  { ticker: "ABNB", name: "Airbnb, Inc.", exchange: "NASDAQ", aliases: ["Airbnb"] },
  { ticker: "UBER", name: "Uber Technologies, Inc.", exchange: "NYSE", aliases: ["Uber"] },
  { ticker: "ARM", name: "Arm Holdings plc", exchange: "NASDAQ", aliases: ["Arm"] },
  { ticker: "SMCI", name: "Super Micro Computer, Inc.", exchange: "NASDAQ", aliases: ["Super Micro"] },
  { ticker: "AMAT", name: "Applied Materials, Inc.", exchange: "NASDAQ", aliases: ["Applied Materials"] },
  { ticker: "MU", name: "Micron Technology, Inc.", exchange: "NASDAQ", aliases: ["Micron"] },
  { ticker: "CSCO", name: "Cisco Systems, Inc.", exchange: "NASDAQ", aliases: ["Cisco"] },
  { ticker: "JPM", name: "JPMorgan Chase & Co.", exchange: "NYSE", aliases: ["JPMorgan", "Chase"] },
  { ticker: "V", name: "Visa Inc.", exchange: "NYSE", aliases: ["Visa"] },
  { ticker: "MA", name: "Mastercard Incorporated", exchange: "NYSE", aliases: ["Mastercard"] },
  { ticker: "BAC", name: "Bank of America Corporation", exchange: "NYSE", aliases: ["Bank of America"] },
  { ticker: "WFC", name: "Wells Fargo & Company", exchange: "NYSE", aliases: ["Wells Fargo"] },
  { ticker: "GS", name: "The Goldman Sachs Group, Inc.", exchange: "NYSE", aliases: ["Goldman Sachs"] },
  { ticker: "BRKB", name: "Berkshire Hathaway Inc.", exchange: "NYSE", aliases: ["Berkshire Hathaway"] },
  { ticker: "WMT", name: "Walmart Inc.", exchange: "NYSE", aliases: ["Walmart"] },
  { ticker: "COST", name: "Costco Wholesale Corporation", exchange: "NASDAQ", aliases: ["Costco"] },
  { ticker: "KO", name: "The Coca-Cola Company", exchange: "NYSE", aliases: ["Coca-Cola", "Coca Cola"] },
  { ticker: "PEP", name: "PepsiCo, Inc.", exchange: "NASDAQ", aliases: ["PepsiCo", "Pepsi"] },
  { ticker: "DIS", name: "The Walt Disney Company", exchange: "NYSE", aliases: ["Disney"] },
  { ticker: "BA", name: "The Boeing Company", exchange: "NYSE", aliases: ["Boeing"] },
  { ticker: "XOM", name: "Exxon Mobil Corporation", exchange: "NYSE", aliases: ["ExxonMobil", "Exxon"] },
  { ticker: "PFE", name: "Pfizer Inc.", exchange: "NYSE", aliases: ["Pfizer"] },
  { ticker: "JNJ", name: "Johnson & Johnson", exchange: "NYSE", aliases: ["Johnson & Johnson"] },
  { ticker: "LLY", name: "Eli Lilly and Company", exchange: "NYSE", aliases: ["Eli Lilly", "Lilly"] },
  { ticker: "UNH", name: "UnitedHealth Group Incorporated", exchange: "NYSE", aliases: ["UnitedHealth"] },
  { ticker: "T", name: "AT&T Inc.", exchange: "NYSE", aliases: ["AT&T", "ATT"] },
  { ticker: "NKE", name: "NIKE, Inc.", exchange: "NYSE", aliases: ["Nike"] },
  { ticker: "MCD", name: "McDonald's Corporation", exchange: "NYSE", aliases: ["McDonald's", "McDonalds"] },
  { ticker: "SBUX", name: "Starbucks Corporation", exchange: "NASDAQ", aliases: ["Starbucks"] },
  { ticker: "HD", name: "The Home Depot, Inc.", exchange: "NYSE", aliases: ["Home Depot"] },
  { ticker: "CAT", name: "Caterpillar Inc.", exchange: "NYSE", aliases: ["Caterpillar"] },
  { ticker: "GE", name: "GE Aerospace", exchange: "NYSE", aliases: ["GE", "General Electric"] },
  { ticker: "SAP", name: "SAP SE", exchange: "NYSE", aliases: ["SAP"] },
  { ticker: "SNY", name: "Sanofi", exchange: "NASDAQ", aliases: ["Sanofi"] },
  { ticker: "SNDK", name: "SanDisk Corporation", exchange: "NASDAQ", aliases: ["SanDisk", "Sandisk"] },
];

export const COMPANIES: readonly CompanyInfo[] = ENTRIES.map((e) => ({
  ticker: e.ticker,
  name: e.name,
  exchange: e.exchange ?? null,
  aliases: e.aliases ?? [],
}));
