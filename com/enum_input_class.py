import enum


# Enums the hv_methods(historical volatility)
class HVMethod(enum.Enum):
    STANDARD_DEVIATION = 1
    PARKINSON_WITH_GAP = 2
    PARKINSON_WITHOUT_GAP = 3
    NATR = 4


# Enum to map candle size to values
class CandleSize(enum.Enum):
    ONE_MIN = "1 min"
    TWO_MIN = "2 mins"
    THREE_MIN = "3 mins"
    FIVE_MIN = "5 mins"
    TEN_MIN = "10 mins"
    FIFTEEN_MIN = "15 mins"
    TWENTY_MIN = "20 mins"
    THIRTY_MIN = "30 mins"
    ONE_HOUR = "1 hour"
    TWO_HOUR = "2 hours"
    THREE_HOUR = "3 hours"
    FOUR_HOUR = "4 hours"
