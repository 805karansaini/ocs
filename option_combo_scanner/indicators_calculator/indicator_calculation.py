import copy
from option_combo_scanner.indicators_calculator.zzz_change_in_iv import ChangeinIV
from option_combo_scanner.indicators_calculator.change_underlying_price import ChangeUnderlyingOptionsPrice
from option_combo_scanner.indicators_calculator.historical_volatility import HistoricalVolatility
from option_combo_scanner.indicators_calculator.implied_volatility import ImpliedVolatility
from option_combo_scanner.indicators_calculator.max_min_pain import Max_Min_Pain
from option_combo_scanner.indicators_calculator.put_call_vol import PutCallVol


class IndicatorCalculation:
    def __init__(self):
        pass
    
    @staticmethod
    def compute_indicators():

        # Historical Volatility
        
        # HistoricalVolatility.compute()
        ImpliedVolatility.compute()
        # PutCallVol.compute()        
        # ChangeUnderlyingOptionsPrice.compute()
        # Max_Min_Pain.compute()


