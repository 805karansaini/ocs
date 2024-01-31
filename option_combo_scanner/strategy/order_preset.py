from pprint import pprint

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.manage_mkt_data_sub import ManageMktDataSubscription
from option_combo_scanner.strategy.monitor_order_preset import MonitorOrderPreset
from option_combo_scanner.strategy.strategy_variables import StrategyVariables as strategy_variables

logger = CustomLogger.logger


class OrderPreset:
    def __init__(
        self,
        values_dict,
        contract,
    ):
        self.unique_id = int(values_dict["UniqueID"])
        self.account_id = values_dict["AccountID"]
        self.ticker = values_dict["Ticker"]
        self.sec_type = values_dict["SecType"]
        self.exchange = values_dict["Exchange"]
        self.currency = values_dict["Currency"]
        self.conid = int(values_dict["Conid"])
        self.risk_percentage = float(values_dict["RiskPercentage"])
        self.risk_dollar = (
            "N/A"
            if values_dict["RiskDollar"] == "N/A"
            else float(values_dict["RiskDollar"])
        )
        try:
            self.net_liquidation_value = float(values_dict["NetLiquidationValue"])
        except:
            self.net_liquidation_value = values_dict["NetLiquidationValue"]

        self.entry_price = float(values_dict["EntryPrice"])
        self.tp1_price = float(values_dict["TP1Price"])
        self.tp2_price = (
            float(values_dict["TP2Price"])
            if values_dict["TP2Price"] not in ["", "N/A", None]
            else None
        )
        self.sl1_price = float(values_dict["SL1Price"])
        self.sl2_price = (
            float(values_dict["SL2Price"])
            if values_dict["SL2Price"] not in ["", "N/A", None]
            else None
        )
        self.entry_quantity = values_dict["EntryQuantity"]
        self.status = values_dict["Status"]
        self.entry_quantity_filled = values_dict["EntryQuantityFilled"]
        self.average_entry_price = values_dict["AverageEntryPrice"]
        self.exit_quantity_filled = values_dict["ExitQuantityFilled"]
        self.average_exit_price = values_dict["AverageExitPrice"]
        self.pnl = values_dict["PNL"]
        self.contract = contract
        self.entry_order_id = values_dict["EntryOrderID"]
        self.flag_entry_order_sent = (
            True if values_dict["FlagEntryOrderSent"] in [1, "1", True] else False
        )
        self.flag_exit_order_sent = (
            True if values_dict["FlagExitOrderSent"] in [1, "1", True] else False
        )
        self.failure_reason = values_dict["FailureReason"]

        # Manage Conid, contract, Subscription
        self.map_unique_id_conid_contract_for_ibapi_ao()

        # Add to the list of unique ids for which entry order is pending, so exit orders can be sent.
        if self.status == "Live":
            if not self.flag_entry_order_sent:
                self.status = "Failed"
                # Mark as failed, if the entry order is not sent
                MonitorOrderPreset.update_order_preset_state(
                    unique_id=self.unique_id,
                    status=self.status,
                )

            elif self.flag_entry_order_sent and not self.flag_exit_order_sent:
                strategy_variables.list_of_unique_ids_for_which_entry_order_is_pending.append(
                    (self.unique_id, int(self.entry_order_id))
                )
            else:
                pass

        # Now Map Subcription id and Manage market data subscription
        ManageMktDataSubscription.subscribe_market_data(self.conid)

        symbol = self.ticker.upper()

        # Add the symbol to the set of symbols for which order execution has been sent
        if self.status not in ["Pending", "Cancelled", "Failed"]:
            strategy_variables.set_symbols_for_which_order_execution_sent.add(symbol)

        # Add to the map_symbol_to_sent_completed_execution
        if symbol in strategy_variables.map_symbol_to_sent_completed_execution:
            pass
        else:
            strategy_variables.map_symbol_to_sent_completed_execution[symbol] = 0

        # Adjust the value of map_symbol_to_sent_completed_execution
        if self.status in ["Live", "Closed"]:
            strategy_variables.map_symbol_to_sent_completed_execution[symbol] += 1

    def map_unique_id_conid_contract_for_ibapi_ao(self):
        # Map unique_id to OrderPreset Object
        variables.map_unique_id_to_order_preset[self.unique_id] = self

        # Map unique_id to conid
        variables.map_unique_id_to_conid[self.unique_id] = self.conid

        # Map conid to contract
        variables.map_conid_to_contract[self.conid] = self.contract

    def __str__(self) -> str:
        return f"OrderPreset:\n{pprint(vars(self))}"

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
