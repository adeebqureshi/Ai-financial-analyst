from __future__ import annotations
from enum import StrEnum
from typing import Final
APP_NAME: Final[str] = "AI Financial Analyst"
APP_VERSION: Final[str] = "0.1.0"
class Environment(StrEnum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"
class LogLevel(StrEnum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
LOG_DIR: Final[str] = "storage/logs"
LOG_FILE_NAME: Final[str] = "app.log"
LOG_MAX_BYTES: Final[int] = 10 * 1024 * 1024
LOG_BACKUP_COUNT: Final[int] = 5
LOG_DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"
LOG_FILE_FORMAT: Final[str] = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d "
    "| request_id=%(request_id)s | %(message)s"
)
LOG_CONSOLE_FORMAT: Final[str] = "%(message)s"
API_DEFAULT_TIMEOUT: Final[int] = 30
API_MAX_RETRIES: Final[int] = 3
API_RETRY_BACKOFF: Final[float] = 0.5
API_RETRY_STATUS_CODES: Final[tuple[int, ...]] = (429, 500, 502, 503, 504)
SEC_API_BASE_URL: Final[str] = "https://www.sec.gov/cgi-bin/browse"
SEC_FULL_TEXT_SEARCH_URL: Final[str] = "https://efts.sec.gov/LATEST/search-index"
FMP_API_BASE_URL: Final[str] = "https://financialmodelingprep.com/api/v3"
OPENAI_API_BASE_URL: Final[str] = "https://api.openai.com/v1"
DB_POOL_SIZE: Final[int] = 10
DB_MAX_OVERFLOW: Final[int] = 20
DB_POOL_TIMEOUT: Final[int] = 30
DB_POOL_RECYCLE: Final[int] = 3600
class FilingType(StrEnum):
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"
    FORM_20F = "20-F"
    FORM_S1 = "S-1"
    FORM_DEF14A = "DEF 14A"
    FORM_13F = "13F-HR"
    FORM_13D = "SC 13D"
    FORM_13G = "SC 13G"
    FORM_4 = "4"
SUPPORTED_FILING_TYPES: Final[frozenset[str]] = frozenset(
    {filing.value for filing in FilingType}
)
FINANCIAL_STATEMENT_SECTIONS: Final[tuple[str, ...]] = (
    "Income Statement",
    "Balance Sheet",
    "Cash Flow Statement",
    "Statement of Stockholders' Equity",
    "Notes to Financial Statements",
)
KEY_FINANCIAL_METRICS: Final[tuple[str, ...]] = (
    "Total Revenue",
    "Gross Profit",
    "Operating Income",
    "Net Income",
    "Earnings Per Share (EPS)",
    "EBITDA",
    "Total Assets",
    "Total Liabilities",
    "Total Stockholders' Equity",
    "Operating Cash Flow",
    "Free Cash Flow",
    "Debt-to-Equity Ratio",
    "Current Ratio",
    "Return on Equity (ROE)",
    "Return on Assets (ROA)",
)
DEFAULT_MARKET_PRIMARY_PROVIDER: Final[str] = "yahoo"
DEFAULT_MARKET_FALLBACK_PROVIDERS: Final[str] = "fmp"
DEFAULT_RISK_FREE_RATE: Final[float] = 0.0425
DEFAULT_MARKET_RETURN: Final[float] = 0.10
DEFAULT_COST_OF_DEBT: Final[float] = 0.05
DEFAULT_TAX_RATE: Final[float] = 0.21
DEFAULT_TERMINAL_GROWTH: Final[float] = 0.03
DEFAULT_PROJECTION_YEARS: Final[int] = 5
SANDBOX_TIMEOUT: Final[int] = 30
SANDBOX_MEMORY_LIMIT_MB: Final[int] = 512
SANDBOX_CPU_LIMIT: Final[float] = 1.0
DEFAULT_EMBEDDING_MODEL: Final[str] = "text-embedding-3-small"
DEFAULT_VECTOR_TOP_K: Final[int] = 5
DEFAULT_ENABLE_RERANKER: Final[bool] = False
DEFAULT_CHUNK_SIZE: Final[int] = 1000
DEFAULT_CHUNK_OVERLAP: Final[int] = 200
DEFAULT_LLM_MODEL: Final[str] = "gpt-4o"
DEFAULT_LLM_TEMPERATURE: Final[float] = 0.0
DEFAULT_LLM_MAX_TOKENS: Final[int] = 4096
DEFAULT_LLM_TOKEN_QUOTA_PER_USER_PER_DAY: Final[int] = 200_000
STORAGE_ROOT: Final[str] = "storage"
RAW_DATA_DIR: Final[str] = "storage/raw"
PARSED_DATA_DIR: Final[str] = "storage/parsed"
EMBEDDINGS_DIR: Final[str] = "storage/embeddings"
CONFIGS_DIR: Final[str] = "configs"