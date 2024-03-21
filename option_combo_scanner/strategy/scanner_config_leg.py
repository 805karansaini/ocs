from pprint import pprint

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.strategy_variables import (
    StrategyVariables as strategy_variables,
)

logger = CustomLogger.logger


class ConfigLeg:
    def __init__(
        self,
        values_dict,
    ):
        [setattr(self, key, value) for key, value in values_dict.items()]

        self.delta_range_max = float(self.delta_range_max)
        self.delta_range_min = float(self.delta_range_min)
        self.dte_range_max = int(self.dte_range_max)
        self.dte_range_min = int(self.dte_range_min)
    #     self.map_configleg_id_to_config_object()

    # def map_configleg_id_to_config_object(self):
    #     # Map leg_number to config leg Object
    #     strategy_variables.map_configleg_id_to_config_object[self.leg_number] = self


    def __str__(self) -> str:
        return f"ConfigLeg: {pprint(vars(self))}"

    
    def get_config_leg_tuple_for_gui(
        self,
    ):
        # Create a tuple with object attributes in the specified order
        config_leg_tuple = (
            self.leg_number,
            self.instrument_id,
            self.action,
            self.right,
            self.delta_range_min,
            self.delta_range_max,
            self.dte_range_min,
            self.dte_range_max,
        )

        return config_leg_tuple
