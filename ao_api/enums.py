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
    QUOTES = "QUOTES"

class OptionRightType(str, Enum):
    CALL = "C"
    PUT = "P"

class DurationUnit(str, Enum):
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"

class TickType(str, Enum):

    ASK = "ASK"
    BID = "BID"
    ASK_SIZE = "ASK_SIZE"
    BID_SIZE = "BID_SIZE"
    OPTION_MODEL = "OPTION_MODEL"
    OPTION_BID = "OPTION_BID"
    OPTION_ASK = "OPTION_ASK"
    OPTION_LAST = "OPTION_LAST"
