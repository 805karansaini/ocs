from pprint import pprint

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.strategy_variables import (
    StrategyVariables as strategy_variables,
)

logger = CustomLogger.logger


class ScannerLeg:
    def __init__(
        self,
        values_dict,
    ):
        [setattr(self, key, value) for key, value in values_dict.items()]

        self.combo_id = int(self.combo_id)
        self.leg_number = int(self.leg_number)
        self.con_id = int(self.con_id)
        self.strike = float(self.strike)
        self.qty = int(self.qty)

    def __str__(self) -> str:
        return f"Scanner Leg Object: {pprint(vars(self))}"
