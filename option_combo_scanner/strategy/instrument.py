from pprint import pprint

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.manage_mkt_data_sub import ManageMktDataSubscription
from option_combo_scanner.strategy.monitor_order_preset import MonitorOrderPreset
from option_combo_scanner.strategy.strategy_variables import StrategyVariables as strategy_variables

logger = CustomLogger.logger


class Instrument:
    def __init__(
        self,
        values_dict,
    ):
        [setattr(self, key, value) for key, value in values_dict.items()]

        # Manage Conid, contract, Subscription
        self.map_instrument_id_to_instrument_object()
        
    def map_instrument_id_to_instrument_object(self):
        # Map instrument_id to Instrument Object
        strategy_variables.map_instrument_id_to_instrument_object[self.instrument_id] = self

    def __str__(self) -> str:
        return f"Instrument:\n{pprint(vars(self))}"

    def change_value(self, key, value):
        """
        Change value of an attribute of this class
        """
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            logger.error(
                f"Inside OrdePreset Object change_value UID: {self.unique_id} '{key}' is not an attribute of this class. new value: {value}"
            )

    def get_instrument_tuple_for_gui(self, ):
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
            self.primary_exchange
        )

        return instrument_tuple

    def remove_from_system(self,):
        del strategy_variables.map_instrument_id_to_instrument_object[self.instrument_id]