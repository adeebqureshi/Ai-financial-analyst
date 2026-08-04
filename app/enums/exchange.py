from enum import Enum


class Exchange(str, Enum):
    NASDAQ = "NASDAQ"
    NYSE = "NYSE"
    AMEX = "AMEX"
    OTHER = "OTHER"