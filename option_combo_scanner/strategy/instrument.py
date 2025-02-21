from pprint import pprint

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.strategy_variables import (
    StrategyVariables as strategy_variables,
)

logger = CustomLogger.logger


class Instrument:
    def __init__(
        self,
        values_dict,
    ):
        [setattr(self, key, value) for key, value in values_dict.items()]

        # Manage Conid, contract, Subscription
        self.map_instrument_id_to_instrument_object()
        self.instrument_id = int(self.instrument_id)

    def map_instrument_id_to_instrument_object(self):
        # Map instrument_id to Instrument Object
        strategy_variables.map_instrument_id_to_instrument_object[
            self.instrument_id
        ] = self

    def __str__(self) -> str:
        attributes_str = ", ".join(
            [f"{key}={value}" for key, value in vars(self).items()]
        )
        return f"Instrument: {attributes_str}"

    def update_attr_value(self, values_dict):
        """
        Change value of an attribute of this class
        """
        for key, value in values_dict.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                logger.error(
                    f"Inside OrdePreset Object change_value UID: {self.unique_id} '{key}' is not an attribute of this class. new value: {value}"
                )

    def get_instrument_tuple_for_gui(
        self,
    ):
        # Create a tuple with object attributes in the specified order
        instrument_tuple = (
            self.instrument_id,
            self.symbol,
            self.sec_type,
            self.multiplier,
            self.exchange,
            self.trading_class,
            self.currency,
            self.conid,
            self.primary_exchange,
        )

        return instrument_tuple

    def remove_from_system(
        self,
    ):
        print(f"Deleteing the instrumen: {self.instrument_id}")
        del strategy_variables.map_instrument_id_to_instrument_object[
            self.instrument_id
        ]
