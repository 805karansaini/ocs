from pprint import pprint

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.strategy_variables import StrategyVariables as strategy_variables

logger = CustomLogger.logger


class Config:
    def __init__(
        self,
        values_dict,
    ):
        [setattr(self, key, value) for key, value in values_dict.items()]

        # Manage Conid, contract, Subscription # TODO
        self.config_id = int(float(self.config_id))
        self.map_config_id_to_config_object()

    def map_config_id_to_config_object(self):

        # Assigning the current object to the 'config_object' variable within the 'strategy_variables'
        strategy_variables.map_config_id_to_config_object[self.config_id] = self

        # Add to min heap
        strategy_variables.primary_min_heap_config.push((-1, self.config_id))

    def __str__(self) -> str:

        return f"Config:\n{pprint(vars(self))}"

    def get_config_tuple_for_gui(
        self,
    ):
        # Create a tuple with object attributes in the specified order
        config_tuple = (
            self.config_id,
            self.no_of_leg,
            # self.right,
            # self.list_of_dte,
            self.list_of_config_leg_object,
        )

        return config_tuple

    def remove_from_system(
        self,
    ):
        print(f"Deleteing the config: {self.config_id}")
        del strategy_variables.map_config_id_to_config_object[self.config_id]
        strategy_variables.primary_min_heap_config.delete_item(self.config_id)
