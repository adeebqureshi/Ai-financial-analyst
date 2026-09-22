from enum import Enum
class FilingType(str, Enum):
    FORM_10K = "10-K"
    FORM_10Q = "10-Q"
    FORM_8K = "8-K"
    FORM_S1 = "S-1"
    FORM_20F = "20-F"
    FORM_6K = "6-K"
    OTHER = "OTHER"