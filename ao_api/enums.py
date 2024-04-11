from enum import Enum


class BarUnit(str, Enum):
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    QUARTER = "quarter"
    YEAR = "year"


class BarType(str, Enum):
    TRADES = "TRADES"
    BID = "BID"
    ASK = "ASK"

class OptionRightType(str, Enum):
    CALL = "C"
    PUT = "P"
