from pprint import pprint

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.manage_mkt_data_sub import ManageMktDataSubscription
from option_combo_scanner.strategy.monitor_order_preset import MonitorOrderPreset
from option_combo_scanner.strategy.strategy_variables import StrategyVariables as strategy_variables

logger = CustomLogger.logger


class ScannerCombination:
    def __init__(self, values_dict,):
        [setattr(self, key, value) for key, value in values_dict.items()]

        #Map combination_id to combination object
        self.map_combo_id_to_scanner_combination_object()

        self.combo_id = int(self.combo_id)
        self.instrument_id = int(self.instrument_id)

    def map_combo_id_to_scanner_combination_object(self):
        
        strategy_variables.map_combo_id_to_scanner_combination_object[self.combo_id] = self

    def __str__(self) -> str:
        
        return f"Scanner Combination Object: {pprint(vars(self))}"
    

    def get_scanner_combination_tuple_for_gui(self, ):
        # Create a tuple with object attributes in the specified order
        combination_tuple = (
            self.combo_id,
            self.instrument_id,
            self.legs,
            self.symbol,
            self.sec_type,
            self.expiry,
            self.right,
            self.multiplier,
            self.trading_class,
            self.currency,
            self.exchange,
            self.combo_net_delta,
            self.list_of_leg_object
        )

        return combination_tuple
