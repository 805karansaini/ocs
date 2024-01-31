import configparser
import copy
import datetime
import tkinter as tk
from tkinter import ttk

import pandas as pd

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.strategy_variables import StrategyVariables

logger = CustomLogger.logger

ORDER_PRESET_COLUMNS = [
    "Unique ID",
    "Ticker",
    "Risk (%)",
    "Risk (USD)",
    "NLV",
    "Entry Price",
    "TP1 Price",
    "TP2 Price",
    "SL1 Price",
    "SL2 Price",
    "Entry Qty",
    "Status",
    "Bid",
    "Ask",
    "Filled Entry Qty",
    "Avg. Entry Price",
    "Filled Exit Qty",
    "Avg. Exit Price",
    "PNL",
    "Failure Reason"
]


class Utils:
    def __init__(self):
        pass

    @staticmethod
    def is_non_negative_number(string):
        try:
            _ = float(string)
            if _ >= 0:
                return True
            return False
        except ValueError:
            return False

    @staticmethod
    def is_non_negative_integer(string):
        try:
            _ = float(string)
            if _ >= 0 and _ % 1 == 0:
                return True
            return False
        except ValueError:
            return False

    @staticmethod
    def is_time(string):
        """
        Should we in HH:MM:SS format
        """
        try:
            datetime.datetime.strptime(string, "%H:%M:%S")
            return True
        except ValueError:
            return False

    @staticmethod
    def display_message_popup(error_title, error_string):
        # Create a message popup window
        message_popup = tk.Toplevel()
        message_popup.title(error_title)

        # Set the geometry of the message popup window
        message_popup.geometry("400x100")

        # Create a frame for the input fields
        message_frame = ttk.Frame(message_popup, padding=20)
        message_frame.pack(fill="both", expand=True)

        char_count = 65
        # Add New Line after every 'char_count' characters
        error_string = "\n".join(
            [
                error_string[i : i + char_count]
                for i in range(0, len(error_string), char_count)
            ]
        )
        # Add labels and entry fields for each column in the table
        error_label = ttk.Label(
            message_frame, text=error_string, width=80, anchor="center"
        )
        error_label.place(relx=0.5, rely=0.5, anchor="center")

    # Calculates the prices of all the combos, and returns them in a dict {unique_id : {BUY: , SELL, total_spread:}
    @staticmethod
    def get_prices_for_order_presets():
        # Making a local copy of unique_id_to_order_preset_obj
        local_unique_id_to_order_preset_obj = copy.deepcopy(
            variables.map_unique_id_to_order_preset
        )

        # Contains all the unique_id and prices, {unique_id : {BUY: , SELL, total_spread:}
        prices_dict = {}

        # Process each order_preset_obj one by one.
        for unique_id, order_preset_obj in local_unique_id_to_order_preset_obj.items():
            con_id = order_preset_obj.conid
            try:
                req_id = variables.map_conid_to_subscripiton_req_id[con_id]
                bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]

                if bid == None:
                    bid = 0
                else:
                    bid = float(bid)

                if ask == None:
                    ask = 0
                else:
                    ask = float(ask)
            except Exception as e:
                logger.error(
                    f"Exception in get_prices_for_order_presets {e} Unique ID: {unique_id} Con ID: {con_id} Req ID: {req_id} Bid: {variables.bid_price[req_id]} Ask: {variables.ask_price[req_id]}"
                )
                continue

            prices_dict[unique_id] = {"Bid": bid, "Ask": ask}

        # Make it available in variables
        variables.unique_id_to_prices_dict = prices_dict

        # print(prices_dict)
        return prices_dict

    @staticmethod
    def create_latest_order_preset_values_dataframe(prices_unique_id):
        # List of update values
        order_preset_table_latest_values = []

        # Making a local copy of unique_id_to_order_preset_obj
        local_unique_id_to_order_preset_obj = copy.deepcopy(
            variables.map_unique_id_to_order_preset
        )

        for unique_id, order_preset_obj in local_unique_id_to_order_preset_obj.items():
            try:
                bid, ask = (
                    prices_unique_id[unique_id]["Bid"],
                    prices_unique_id[unique_id]["Ask"],
                )
            except Exception as e:
                bid, ask = None, None
                logger.error(
                    f"Exception in create latest order preset {e} UID: {unique_id} Bid: {bid} Ask: {ask}"
                )

            row_value = Utils.get_tuple_values_for_order_preset_row(
                order_preset_obj, bid, ask
            )

            order_preset_table_latest_values.append(row_value)

        # Create dataframe
        order_preset_table_latest_values_dataframe = pd.DataFrame(
            order_preset_table_latest_values, columns=ORDER_PRESET_COLUMNS
        )

        return order_preset_table_latest_values_dataframe

    @staticmethod
    def update_setting_in_system(
        number_of_trades_allowed: int,
        max_ba_spread: float,
        price_gap_threshold: float,
        stoploss_threshold: float,
        number_of_iterations: int,
        sleep_time_between_iterations: float,
        trade_start_time: str,
        trade_end_time: str,
        max_nlv_exposure_per_trade: float,
    ):
        # Set the values for attributes
        setattr(StrategyVariables, "number_of_trades_allowed", number_of_trades_allowed)
        setattr(StrategyVariables, "max_ba_spread", max_ba_spread)
        setattr(StrategyVariables, "price_gap_threshold", price_gap_threshold)
        setattr(StrategyVariables, "stoploss_threshold", stoploss_threshold)
        setattr(StrategyVariables, "number_of_iterations", number_of_iterations)
        setattr(
            StrategyVariables,
            "sleep_time_between_iterations",
            sleep_time_between_iterations,
        )
        setattr(StrategyVariables, "trade_start_time", trade_start_time)
        setattr(StrategyVariables, "trade_end_time", trade_end_time)
        setattr(
            StrategyVariables, "max_nlv_exposure_per_trade", max_nlv_exposure_per_trade
        )

    @staticmethod
    def update_settings_in_config_file(
        number_of_trades_allowed,
        max_ba_spread,
        price_gap_threshold,
        stoploss_threshold,
        number_of_iterations,
        sleep_time_between_iterations,
        trade_start_time,
        trade_end_time,
        max_nlv_exposure_per_trade,
    ):
        # Read the config file
        config = configparser.ConfigParser()
        config.read("config.ini")

        # Update the values
        config["ExecutionEngine"]["number_of_trades_allowed"] = str(
            number_of_trades_allowed
        )
        config["ExecutionEngine"]["max_ba_spread"] = str(max_ba_spread)
        config["ExecutionEngine"]["price_gap_threshold"] = str(price_gap_threshold)
        config["ExecutionEngine"]["stoploss_threshold"] = str(stoploss_threshold)
        config["ExecutionEngine"]["number_of_iterations"] = str(number_of_iterations)
        config["ExecutionEngine"]["sleep_time_between_iterations"] = str(
            sleep_time_between_iterations
        )
        config["ExecutionEngine"]["trade_start_time"] = str(trade_start_time)
        config["ExecutionEngine"]["trade_end_time"] = str(trade_end_time)
        config["ExecutionEngine"]["max_nlv_exposure_per_trade"] = str(
            max_nlv_exposure_per_trade
        )

        # Write the config file
        with open("config.ini", "w") as configfile:
            config.write(configfile)

    @staticmethod
    def get_tuple_values_for_order_preset_row(order_preset_obj, bid=None, ask=None):
        unique_id = order_preset_obj.unique_id
        ticker = order_preset_obj.ticker
        risk_percentage = order_preset_obj.risk_percentage
        risk_dollar = order_preset_obj.risk_dollar
        net_liquidation_value = order_preset_obj.net_liquidation_value
        entry_price = order_preset_obj.entry_price
        tp1_price = order_preset_obj.tp1_price
        tp2_price = order_preset_obj.tp2_price
        sl1_price = order_preset_obj.sl1_price
        sl2_price = order_preset_obj.sl2_price
        entry_quantity = order_preset_obj.entry_quantity
        status = order_preset_obj.status
        entry_quantity_filled = order_preset_obj.entry_quantity_filled
        average_entry_price = order_preset_obj.average_entry_price
        exit_quantity_filled = order_preset_obj.exit_quantity_filled
        average_exit_price = order_preset_obj.average_exit_price
        pnl = order_preset_obj.pnl
        failure_reason = order_preset_obj.failure_reason

        try:
            realised_pnl = (
                average_exit_price - average_entry_price
            ) * exit_quantity_filled
        except Exception as e:
            realised_pnl = None

        try:
            ba_mid = (bid + ask) / 2
            unrealised_pnl = (ba_mid - average_entry_price) * (
                entry_quantity_filled - exit_quantity_filled
            )
        except Exception as e:
            unrealised_pnl = None

        # Format the values here
        try:
            risk_percentage = f"{float(risk_percentage):,.2f}"
        except Exception as e:
            pass

        try:
            risk_dollar = f"{float(risk_dollar):,.2f}"
        except Exception as e:
            pass

        try:
            net_liquidation_value = f"{float(net_liquidation_value):,.2f}"
        except Exception as e:
            pass

        try:
            entry_price = f"{float(entry_price):,.2f}"
        except Exception as e:
            pass

        try:
            tp1_price = f"{float(tp1_price):,.2f}"
        except Exception as e:
            pass

        try:
            tp2_price = f"{float(tp2_price):,.2f}"
        except Exception as e:
            pass

        try:
            sl1_price = f"{float(sl1_price):,.2f}"
        except Exception as e:
            pass

        try:
            sl2_price = f"{float(sl2_price):,.2f}"
        except Exception as e:
            pass

        try:
            entry_quantity = f"{float(entry_quantity):,.2f}"
        except Exception as e:
            pass

        try:
            bid = f"{float(bid):,.2f}"
        except Exception as e:
            pass

        try:
            ask = f"{float(ask):,.2f}"
        except Exception as e:
            pass

        try:
            entry_quantity_filled = f"{float(entry_quantity_filled):,}"
        except Exception as e:
            pass

        try:
            average_entry_price = f"{float(average_entry_price):,.2f}"
        except Exception as e:
            pass

        try:
            exit_quantity_filled = f"{float(exit_quantity_filled):,}"
        except Exception as e:
            pass

        try:
            average_exit_price = f"{float(average_exit_price):,.2f}"
        except Exception as e:
            pass

        try:
            if (unrealised_pnl is not None) and (realised_pnl is not None):
                pnl = f"{float(unrealised_pnl + realised_pnl):,.2f}"
        except Exception as e:
            pass

        return (
            unique_id,
            ticker,
            risk_percentage,
            risk_dollar,
            net_liquidation_value,
            entry_price,
            tp1_price,
            tp2_price,
            sl1_price,
            sl2_price,
            entry_quantity,
            status,
            bid,
            ask,
            entry_quantity_filled,
            average_entry_price,
            exit_quantity_filled,
            average_exit_price,
            pnl,
            failure_reason,
        )
