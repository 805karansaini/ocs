from pprint import pprint

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.manage_mkt_data_sub import ManageMktDataSubscription
from option_combo_scanner.strategy.monitor_order_preset import MonitorOrderPreset
from option_combo_scanner.strategy.strategy_variables import StrategyVariables as strategy_variables

logger = CustomLogger.logger


class ConfigLeg:
    def __init__(
        self,
        values_dict,
    ):
        [setattr(self, key, value) for key, value in values_dict.items()]

        self.delta_range_max = float(self.delta_range_max)
        self.delta_range_min = float(self.delta_range_min)
    
    def __str__(self) -> str:
        return f"ConfigLeg: {pprint(vars(self))}"

    def change_value(self, key, value):
        """
        Change value of an attribute of this class
        """
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            # TODO 
            logger.error(
                f"Inside OrdePreset Object change_value UID: {self.unique_id} '{key}' is not an attribute of this class. new value: {value}"
            )

    def get_config_leg_tuple_for_gui(self, ):
        # Create a tuple with object attributes in the specified order
        config_leg_tuple = (
            self.leg_number,
            self.action,
            self.delta_range_min,
            self.delta_range_max
        )

        return config_leg_tuple