from pprint import pprint

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.manage_mkt_data_sub import ManageMktDataSubscription
from option_combo_scanner.strategy.monitor_order_preset import MonitorOrderPreset
from option_combo_scanner.strategy.strategy_variables import StrategyVariables as strategy_variables

logger = CustomLogger.logger


class Indicator:
    def __init__(self, values_dict,):
        [setattr(self, key, value) for key, value in values_dict.items()]

        self.indicator_id = int(self.indicator_id)
        self.map_indicator_id_to_indicator_object()

        
    def map_indicator_id_to_indicator_object(self):
        
        # Assigning the current object to the 'indicator_object' variable within the 'strategy_variables'
        strategy_variables.map_indicator_id_to_indicator_object[self.indicator_id] = self

    def __str__(self) -> str:
        
        return f"Indicator:\n{pprint(vars(self))}"
    
    def get_indicator_tuple_for_gui(self, ):
        # Create a tuple with object attributes in the specified order
        indicator_tuple = (
            self.indicator_id,
            self.symbol,
            self.expiry,
            self.hv,
            self.iv,
            self.hv_iv,
            self.rr_25,
            self.rr_50,
            self.rr_25_50,
            self.rr_change_last_close,
            self.max_pain,
            self.min_pain, 
            self.avg_iv, 
            self.avg_hv, 
            self.open_interest_support, 
            self.open_interest_resistance, 
            self.put_volume, 
            self.call_volume, 
            self.put_call_volume_ratio, 
            self.put_call_volume_average,
            self.change_underlying_option_price, 
            self.change_underlying_option_price_14_days, 
            self.pc_change, 
            self.iv_change, 
            self.pc_change_iv_change

        )

        return indicator_tuple
