import threading
import tkinter as tk
from tkinter import Scrollbar, ttk

from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.strategy_variables import StrategyVariables


class OrderPresetHelper:
    def __init__(self, order_presets_table) -> None:
        self.order_presets_table = order_presets_table

    def remove_preset_from_table(self, unique_id):
        self.order_presets_table.delete(unique_id)

    def validate_preset_order_inputs(
        self,
        ticker,
        nlv,
        entry_price,
        risk_percent,
        tp1_price,
        sl1_price,
        tp2_price,
        sl2_price,
    ):
        # Validate the input fields
        if (
            ticker == ""
            or nlv == ""
            or entry_price == ""
            or risk_percent == ""
            or tp1_price == ""
            or sl1_price == ""
        ):
            Utils.display_message_popup(
                "Error",
                "Please fill all the fields: Ticker, NLV, Entry Price, Risk %, TP1 Price, SL1 Price",
            )
            return False

        # validate is Float
        if (
            not Utils.is_non_negative_number(nlv)
            or not Utils.is_non_negative_number(entry_price)
            or not Utils.is_non_negative_number(risk_percent)
            or not Utils.is_non_negative_number(tp1_price)
            or not Utils.is_non_negative_number(sl1_price)
        ):
            Utils.display_message_popup(
                "Error",
                "Please enter valid values for NLV, Entry Price, Risk %, TP1 Price, SL1 Price.\nAll values should be non-negatve numbers.",
            )
            return False

        # TP1 should be greater than Entry Price
        if float(entry_price) >= float(tp1_price):
            Utils.display_message_popup(
                "Error",
                "TP1 Price should be greater than Entry Price",
            )
            return False

        # SL1 should be lessthan Entry Price
        if float(entry_price) <= float(sl1_price):
            Utils.display_message_popup(
                "Error",
                "SL1 Price should be less than Entry Price",
            )
            return False

        # SL Threshold
        stoploss_threshold = StrategyVariables.stoploss_threshold / 100

        # Check that sl1 is not more than 10% below the entry price
        if (
            float(entry_price) - float(sl1_price)
            >= float(entry_price) * stoploss_threshold
        ):
            Utils.display_message_popup(
                "Error",
                "SL1 Price is too far below the Entry Price. Please adjust the SL1 Price.",
            )
            return False

        # if TP2 exists, then validate TP2 > TP1
        if tp2_price != "":
            # Validate is Float
            if not Utils.is_non_negative_number(tp2_price):
                Utils.display_message_popup(
                    "Error",
                    "Please enter valid values for TP2 Price.\nValue should be non-negatve numbers.",
                )
                return False

            # Validate TP2 > TP1
            if float(tp2_price) <= float(tp1_price):
                Utils.display_message_popup(
                    "Error",
                    "TP2 Price should be greater than TP1 Price",
                )
                return False

        # if SL2 exists, then validate SL2 > SL1
        if sl2_price != "":
            # Validate is Float
            if not Utils.is_non_negative_number(sl2_price):
                Utils.display_message_popup(
                    "Error",
                    "Please enter valid values for SL2 Price.\nValue should be non-negatve numbers.",
                )
                return False

            # Validate SL2 > SL1
            if float(sl2_price) <= float(sl1_price):
                Utils.display_message_popup(
                    "Error",
                    "SL2 Price should be greater than SL1 Price",
                )
                return False

        return True

    def add_order_preset_to_table(
        self,
        values_dict,
    ):
        # Add the row to the table.
        row_values = (
            values_dict.get("UniqueID", "N/A"),
            values_dict.get("Ticker", "N/A"),
            values_dict.get("RiskPercentage", "N/A"),
            values_dict.get("RiskDollar", "N/A"),
            values_dict.get("NetLiquidationValue", "N/A"),
            values_dict.get("EntryPrice", "N/A"),
            values_dict.get("TP1Price", "N/A"),
            values_dict.get("SL1Price", "N/A"),
            "None"
            if values_dict.get("TP2Price", "N/A") == ""
            else values_dict.get("TP2Price", "N/A"),
            "None"
            if values_dict.get("SL2Price", "N/A") == ""
            else values_dict.get("SL2Price", "N/A"),
            # values_dict.get("SL2Price", "N/A"),
            values_dict.get("EntryQuantity", "N/A"),
            values_dict.get("Status", "Pending"),
            values_dict.get("Bid", "N/A"),
            values_dict.get("Ask", "N/A"),
            values_dict.get("EntryQuantityFilled", "N/A"),
            values_dict.get("AverageEntryPrice", "N/A"),
            values_dict.get("ExitQuantityFilled", "N/A"),
            values_dict.get("AverageExitPrice", "N/A"),
            values_dict.get("PNL", "N/A"),
            values_dict.get("FailureReason", "N/A"),
        )

        # Get the current number of items in the treeview
        num_items = len(self.order_presets_table.get_children())

        if num_items % 2 == 1:
            self.order_presets_table.insert(
                "",
                "end",
                iid=values_dict.get("UniqueID", "N/A"),
                text=num_items + 1,
                values=row_values,
                tags=("oddrow",),
            )
        else:
            self.order_presets_table.insert(
                "",
                "end",
                iid=values_dict.get("UniqueID", "N/A"),
                text=num_items + 1,
                values=row_values,
                tags=("evenrow",),
            )

    def update_order_preset_table(self, order_preset_table_values_df):
        # All the rows in Order Preset Table
        unique_id_in_order_preset_table = self.order_presets_table.get_children()

        # Update the rows
        for i, row_val in order_preset_table_values_df.iterrows():
            # Unique ID of row val
            unique_id = row_val["Unique ID"]

            # Tuple of vals
            row_val = tuple(order_preset_table_values_df.iloc[i])

            # If this unique_id in Table update the values
            if str(unique_id) in unique_id_in_order_preset_table:
                # Update the row at once.
                self.order_presets_table.item(unique_id, values=row_val)

        # Row counter
        counter_row = 0

        # Move According to data Color here, Change Color
        for i, row in order_preset_table_values_df.iterrows():
            # Unique_id
            unique_id = str(row["Unique ID"])

            # If unique_id in table
            if unique_id in unique_id_in_order_preset_table:
                self.order_presets_table.move(unique_id, "", counter_row)

                if counter_row % 2 == 0:
                    self.order_presets_table.item(unique_id, tags="evenrow")
                else:
                    self.order_presets_table.item(unique_id, tags="oddrow")

                # Increase row count
                counter_row += 1
