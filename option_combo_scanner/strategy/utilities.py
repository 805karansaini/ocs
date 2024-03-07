import copy
import datetime

import pandas as pd
import pytz

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.strategy_variables import (
    StrategyVariables as strategy_variables,
)

logger = CustomLogger.logger


class StrategyUtils:
    def __init__(self):
        pass

    @staticmethod
    def calculate_entry_qty_and_risk_dollar(risk_percent, current_ba_mid, sl1_price):
        entry_qty, risk_dollar = None, None
        try:
            account_nlv = copy.deepcopy(
                variables.map_account_id_to_nlv[variables.account_id]
            )
            risk_dollar = int((account_nlv * risk_percent) / 100)

            loss_per_share = abs(current_ba_mid - sl1_price)

            # Calculate entry qty
            entry_qty = risk_dollar / loss_per_share

            # Calculate the entry qty based on the max exposure
            max_exposure = strategy_variables.max_nlv_exposure_per_trade
            max_exposure_dollar = int((account_nlv * max_exposure) / 100)
            max_exposure_qty = max_exposure_dollar / current_ba_mid
            entry_qty = min(entry_qty, max_exposure_qty)

            # If fractional shares are not enabled, then round the entry qty
            entry_qty = round(entry_qty)

        except Exception as e:
            pass

        return entry_qty, risk_dollar

    @staticmethod
    def get_account_nlv():
        account_nlv = copy.deepcopy(
            variables.map_account_id_to_nlv[variables.account_id]
        )

        if account_nlv is not None:
            account_nlv = int(account_nlv)

        return account_nlv

    @staticmethod
    def cancel_pending_preset_order(unique_id: int):
        # Check if the order is already pending
        if variables.map_unique_id_to_order_preset[unique_id].status == "Pending":
            # Update the order status
            variables.map_unique_id_to_order_preset[unique_id].change_value(
                "status", "Cancelled"
            )

            values_dict = {"Status": "Cancelled"}
            where_clause = f"WHERE UniqueID={unique_id}"
            SqlQueries.update_preset_order(values_dict, where_clause=where_clause)
            logger.info(f"Preset Order with UID: {unique_id} canceled")

    @staticmethod
    def cancel_all_pending_preset_orders():
        for unique_id in variables.map_unique_id_to_order_preset.keys():
            StrategyUtils.cancel_pending_preset_order(unique_id)

    @staticmethod
    def update_the_values_for_order_preset_table(unique_id=None, order_id=None):
        """
        The Method will be used to calculate the
        entry/exit price
        &
        entry/exit quantity filled
        status
        """
        try:
            # Get all the orders
            all_orders_dict = SqlQueries.get_orders("*")

            # Create a dataframe from the orders
            all_orders_df = pd.DataFrame.from_dict(all_orders_dict)

            # If dataframes is empty, return
            if all_orders_df.empty:
                return

            # Log
            logger.debug(f"All Orders:\n {all_orders_df.to_string()}")

            # Group Order with the same unique_id
            grouped_orders_df = all_orders_df.groupby(["UniqueID"])

            # Now loop over each group, and compute
            # EntryQuantityFilled, AverageEntryPrice, ExitQuantityFilled, AverageExitPrice,
            #  if OrderType is MKT and Action is BUY and OrderStatus is Filled, then EntryQuantityFilled = FillledQuantity,  AverageEntryPrice  = AverageFillPrice
            # if OrderType is LMT/STP and Action is SELL and OrderStatus is Filled, then ExitQuantityFilled += FillledQuantity,  AverageExitPrice  = WeightedAvgof AverageFillPrice

            # Loop over each group
            for unique_id, group in grouped_orders_df:
                try:
                    unique_id = int(unique_id[0])
                    order_preset_obj = variables.map_unique_id_to_order_preset[
                        unique_id
                    ]
                    flag_exit_order_sent = order_preset_obj.flag_exit_order_sent
                    status = order_preset_obj.status
                    if status not in ["Live"]:
                        continue

                    entry_quantity_filled = 0
                    average_entry_price = 0

                    exit_quantity_filled = 0
                    average_exit_price = 0
                    order_preset_status = "Closed"

                    # Calculate the values
                    for index, row in group.iterrows():
                        order_type = row["OrderType"]
                        action = row["Action"]
                        order_status = row["OrderStatus"]
                        filled_quantity = row["FilledQuantity"]
                        average_fill_price = row["AverageFillPrice"]

                        if (
                            order_type == "MKT"
                            and action == "BUY"
                            and order_status == "Filled"
                        ):
                            entry_quantity_filled = float(filled_quantity)
                            average_entry_price = float(average_fill_price)
                        elif (
                            (order_type == "LMT" or order_type == "STP")
                            and action == "SELL"
                            and order_status == "Filled"
                        ):
                            exit_quantity_filled += float(filled_quantity)
                            average_exit_price += float(filled_quantity) * float(
                                average_fill_price
                            )

                        if flag_exit_order_sent and order_status in [
                            "Cancelled",
                            "Filled",
                            "Inactive",
                        ]:
                            pass
                        else:
                            order_preset_status = None

                    # Calculate the average exit price
                    if exit_quantity_filled > 0:
                        average_exit_price /= exit_quantity_filled

                    # Update the values in the database
                    values_dict = {
                        "EntryQuantityFilled": entry_quantity_filled,
                        "AverageEntryPrice": average_entry_price,
                        "ExitQuantityFilled": exit_quantity_filled,
                        "AverageExitPrice": average_exit_price,
                    }

                    # Calculate the status
                    if order_preset_status is not None:
                        values_dict["Status"] = order_preset_status

                    where_clause = f" WHERE UniqueID={unique_id}"
                    SqlQueries.update_preset_order(
                        values_dict, where_clause=where_clause
                    )

                    unique_id = int(unique_id)

                    # Update the values in the order preset objects
                    if unique_id in variables.map_unique_id_to_order_preset:
                        order_preset = variables.map_unique_id_to_order_preset[
                            unique_id
                        ]

                        for key, value in values_dict.items():
                            converted_key = "".join(
                                ["_" + c.lower() if c.isupper() else c for c in key]
                            )
                            converted_key = converted_key.lstrip("_")

                            order_preset.change_value(converted_key, value)
                except Exception as e:
                    logger.error(
                        f"Exception in update_the_values_for_order_preset_table loop UID: {unique_id} update_the_values_for_order_preset_table: {e}"
                    )

        except Exception as e:
            logger.error(f"Exception in update_the_values_for_order_preset_table: {e}")

    @staticmethod
    def do_time_check_for_monitoring():
        try:
            target_time_zone = strategy_variables.target_time_zone
            trade_start_time = strategy_variables.trade_start_time
            trade_end_time = strategy_variables.trade_end_time

            # Timezone object for the target time zone
            target_timezone_object = pytz.timezone(target_time_zone)
            current_time_in_target_time_zone = datetime.datetime.now(
                target_timezone_object
            )

            # Get today's date in the target time zone
            today_date = datetime.datetime.now(target_timezone_object).date()

            # Parse the start and end times and combine with today's date
            start_time_in_target_time_zone = target_timezone_object.localize(
                datetime.datetime.strptime(
                    str(today_date) + " " + trade_start_time, "%Y-%m-%d %H:%M:%S"
                )
            )
            end_time_in_target_time_zone = target_timezone_object.localize(
                datetime.datetime.strptime(
                    str(today_date) + " " + trade_end_time, "%Y-%m-%d %H:%M:%S"
                )
            )

            if (
                start_time_in_target_time_zone
                <= current_time_in_target_time_zone
                <= end_time_in_target_time_zone
            ):
                return True

        except Exception as e:
            logger.error(f"Exception in do_time_check_for_monitoring: {e}")

        return False
