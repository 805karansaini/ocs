import copy
import datetime
import threading
import time

import pandas as pd

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.database.sql_queries import SqlQueries

# from gui.gui import IsScreenRunning Used in local import tho avoid circular imports
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.order_generator import OrderGenerator
from option_combo_scanner.strategy.strategy_variables import StrategyVariables as strategy_variables
from option_combo_scanner.strategy.utilities import StrategyUtils

logger = CustomLogger.logger


class MonitorOrderPreset:
    def __init__(
        self,
    ):
        pass

    def monitor_and_execute(
        self,
    ):
        """
        Monitor the OrderPreset and execute the order if the conditions are met

        Steps:
            Check if the OrderPreset is pending
            Check if ticker price is greater than entry price
            send order to execution module in a separate thread
        """

        local_map_unique_id_to_order_preset = variables.map_unique_id_to_order_preset
        for (
            unique_id,
            order_preset_obj,
        ) in local_map_unique_id_to_order_preset.items():
            unique_id = int(unique_id)
            # Get Values
            entry_price = float(order_preset_obj.entry_price)
            conid = order_preset_obj.conid
            status = order_preset_obj.status
            risk_percent = order_preset_obj.risk_percentage
            sl1_price = order_preset_obj.sl1_price

            # Check if the OrderPreset is pending
            if status == "Pending":
                try:
                    # Check if ticker price is greater than entry price
                    reqid = variables.map_conid_to_subscripiton_req_id[conid]
                    bid, ask = variables.bid_price[reqid], variables.ask_price[reqid]
                    ba_mid = (bid + ask) / 2
                except Exception as e:
                    logger.error(
                        f"Monitoring UID: {unique_id} Exception while monitoring could not compute ba-mid {e} Bid: {bid} Ask: {ask}"
                    )
                    continue

                # Log
                logger.info(
                    f" UID: {unique_id} Status: {status} entry_price: {entry_price} ba_mid: {ba_mid} bid: {bid} ask: {ask}"
                )

                if ba_mid >= entry_price:
                    status = "Live"

                    (
                        total_qty,
                        risk_dollar,
                    ) = StrategyUtils.calculate_entry_qty_and_risk_dollar(
                        risk_percent=risk_percent,
                        current_ba_mid=ba_mid,
                        sl1_price=sl1_price,
                    )

                    # Get the latest nlv
                    nlv = StrategyUtils.get_account_nlv()

                    if total_qty == 0:
                        # Update the database and order preset object
                        MonitorOrderPreset.update_order_preset_state(
                            unique_id,
                            "Failed",
                            0,
                            failure_reason="Total Order Qty was 0",
                        )
                        continue
                    elif risk_dollar is None:
                        # Update the database and order preset object
                        MonitorOrderPreset.update_order_preset_state(
                            unique_id,
                            "Failed",
                            0,
                            failure_reason="Risk (USD) computation failed.",
                        )
                        continue

                    elif total_qty == None:
                        # Update the database and order preset object
                        MonitorOrderPreset.update_order_preset_state(
                            unique_id,
                            "Failed",
                            0,
                            failure_reason="Total Order Qty computation failed.",
                        )
                        continue

                    # Update the database and order preset object
                    MonitorOrderPreset.update_order_preset_state(
                        unique_id, status, total_qty, risk_dollar=risk_dollar, nlv=nlv
                    )

                    # Log
                    logger.info(
                        f"Monitoring UID: {unique_id} Order Preset Status Updated: {order_preset_obj.status}"
                    )

                    # Send order preset to execution engine in a separate thread
                    execution_engine_thread = threading.Thread(
                        target=self.execution_engine, args=(unique_id,)
                    )
                    execution_engine_thread.start()

    def execute_order(self, order_preset_obj):
        # Get Values
        unique_id = order_preset_obj.unique_id
        entry_qty = order_preset_obj.entry_quantity
        tp1_price = order_preset_obj.tp1_price
        tp2_price = order_preset_obj.tp2_price
        sl1_price = order_preset_obj.sl1_price
        sl2_price = order_preset_obj.sl2_price
        conid = order_preset_obj.conid

        contract = variables.map_conid_to_contract[conid]
        symbol = contract.symbol
        flag_can_send_order = False

        # Start of critical section
        with strategy_variables.order_execution_lock:
            count = 0
            ticker_set = set()
            for (
                ticker,
                value,
            ) in strategy_variables.map_symbol_to_sent_completed_execution.items():
                if value > 0:
                    count += 1
                    ticker_set.add(ticker)

            # Check if we can send the order or not
            if (count < strategy_variables.number_of_trades_allowed) or (
                symbol in ticker_set
            ):
                strategy_variables.map_symbol_to_sent_completed_execution[symbol] += 1
                flag_can_send_order = True
            else:
                flag_can_send_order = False
        # End of critical section

        # Send the order for execution
        if flag_can_send_order:
            entry_mkt_order = OrderGenerator.get_entry_order_for_strategy(
                entry_qty=entry_qty
            )
            entry_order_id = entry_mkt_order.orderId

            # Send the entry order to tws, also save the order in the database
            MonitorOrderPreset.send_order_to_tws(unique_id, contract, entry_mkt_order)

            # Update the database and order preset object
            MonitorOrderPreset.update_order_preset_state(
                unique_id,
                "Live",
                entry_qty,
                flag_entry_order_sent=True,
                entry_order_id=entry_order_id,
            )

            strategy_variables.list_of_unique_ids_for_which_entry_order_is_pending.append(
                (unique_id, entry_order_id)
            )

        else:
            # Mark failed as the day entry limit has been reached
            MonitorOrderPreset.update_order_preset_state(
                unique_id,
                "Failed",
                entry_qty,
                failure_reason="The Max # of Trades has been reached.",
            )

    def execution_engine(self, unique_id):
        # Spawn a new(execution_engine) thread everytime the entry condition is met.
        # Inside that thread we need to implement the execution logic
        # which checks for the ba-spread, and if spread is not meet we again want to fetch the latest prices again check the spread and entry price condition
        # Checks if the order can be executed or not limit for trades has been reached
        # Checks if the speard is in limit

        # Local Import Here, to avoid the circular import
        from gui.gui import IsScreenRunning

        order_preset_obj = variables.map_unique_id_to_order_preset[unique_id]
        conid = int(order_preset_obj.conid)
        reqid = variables.map_conid_to_subscripiton_req_id[conid]
        unique_id = order_preset_obj.unique_id

        count = 0

        flag_high_spread = False
        flag_too_high_above_entry_price = False

        while (
            count < strategy_variables.number_of_iterations
        ) and IsScreenRunning.flag_is_screen_running:
            flag_high_spread = False
            flag_too_high_above_entry_price = False

            current_bid, current_ask = (
                variables.bid_price[reqid],
                variables.ask_price[reqid],
            )

            current_ba_mid = (current_bid + current_ask) / 2
            current_spread = abs(current_bid - current_ask)

            # Get the price gap threshold
            price_gap_threshold = strategy_variables.price_gap_threshold
            price_gap_threshold /= 100

            entry_price = float(order_preset_obj.entry_price)
            upper_limit = entry_price * (1 + price_gap_threshold)

            allowed_spread_percentage = strategy_variables.max_ba_spread / 100
            max_spread_value = allowed_spread_percentage * current_ba_mid

            # Perform Check if we can send the order or not
            if (current_ba_mid <= upper_limit) and (current_spread <= max_spread_value):
                # Send the order for execution
                self.execute_order(order_preset_obj)
                break
            elif current_ba_mid > upper_limit:
                flag_too_high_above_entry_price = True
                logger.info(
                    f"Try: {count+1}/{strategy_variables.number_of_iterations} UID: {order_preset_obj.unique_id} Failed to send order as Current BA Mid: {current_ba_mid} is higher than Upper Price Limit: {upper_limit}, Entry Price: {entry_price} % Above Entry Price: {strategy_variables.price_gap_threshold}"
                )
            elif current_spread > max_spread_value:
                flag_high_spread = True
                logger.info(
                    f"Try: {count+1}/{strategy_variables.number_of_iterations} UID: {order_preset_obj.unique_id} Failed to send order as Current Spread: {current_spread} is higher than Max Spread Limit: {max_spread_value}, % Spread: {strategy_variables.max_ba_spread} Ask: {current_ask} Bid: {current_bid}"
                )
            else:
                logger.info(
                    f"Try: {count+1}/{strategy_variables.number_of_iterations} UID: {order_preset_obj.unique_id} Failed to send order. current_ba_mid: {current_ba_mid} upper_limit: {upper_limit} max_spread_value: {max_spread_value} current_spread: {current_spread}"
                )

            time.sleep(strategy_variables.sleep_time_between_iterations)
            count += 1
        else:
            if flag_high_spread:
                failure_reason = "The spread exceeded the permissible spread limit."
            elif flag_too_high_above_entry_price:
                failure_reason = "BA Mid surpassed the Upper Price Limit."
            else:
                failure_reason = "The application was closed."

            # Mark failed as the day entry limit has been reached
            MonitorOrderPreset.update_order_preset_state(
                order_preset_obj.unique_id, "Failed", 0, failure_reason=failure_reason
            )
            # Log
            logger.info(
                f"UID: {order_preset_obj.unique_id} Failed to send order. current_ba_mid: {current_ba_mid} upper_limit: {upper_limit} max_spread_value: {max_spread_value} current_spread: {current_spread}"
            )

    @staticmethod
    def send_order_to_tws(unique_id, contract, order):
        variables.app.placeOrder(
            order.orderId,
            contract,
            order,
        )

        values_dict = {}
        values_dict["OrderID"] = order.orderId
        values_dict["UniqueID"] = unique_id
        values_dict["AccountID"] = variables.account_id
        values_dict["Ticker"] = contract.symbol
        values_dict["Action"] = order.action
        values_dict["OrderType"] = order.orderType
        if order.orderType == "STP":
            values_dict["OrderPrice"] = order.auxPrice
        elif order.orderType == "LMT":
            values_dict["OrderPrice"] = order.lmtPrice
        else:
            values_dict["OrderPrice"] = "N/A"
        values_dict["OrderQuantity"] = order.totalQuantity

        # YYYY-MM-DD HH:MM:SS
        formatted_current_time = datetime.datetime.now(
            variables.target_timezone_obj
        ).strftime("%Y-%m-%d %H:%M:%S")
        values_dict["OrderTime"] = formatted_current_time
        values_dict["LastUpdateTime"] = formatted_current_time

        values_dict["OrderStatus"] = "Sent"
        values_dict["FilledQuantity"] = 0
        values_dict["AverageFillPrice"] = 0
        values_dict["OrderRef"] = order.orderRef
        values_dict["OCAGroup"] = order.ocaGroup
        values_dict["OCAType"] = order.ocaType
        values_dict["FailureReason"] = "N/A"
        values_dict["FlagPurged"] = 0

        # Insert into orders table
        SqlQueries.insert_into_orders(values_dict)

        # Insert the order into the order book
        strategy_variables.screen.order_book_tab_object.insert_order_preset_status_order_book(
            values_dict
        )

    def send_exit_orders(
        self,
    ):
        N = len(strategy_variables.list_of_unique_ids_for_which_entry_order_is_pending)

        for index in range(N - 1, -1, -1):
            (
                unique_id,
                entry_order_id,
            ) = strategy_variables.list_of_unique_ids_for_which_entry_order_is_pending[
                index
            ]
            unique_id = int(unique_id)
            entry_order_id = int(entry_order_id)

            # Get the order status from db
            columns = "OrderStatus"
            where_clause = f"WHERE OrderID = {entry_order_id}"
            order_status_res = SqlQueries.get_orders(columns, where_clause)

            # Log
            logger.debug(f"UID: {unique_id} Entry Order Status: {order_status_res}")

            try:
                order_status = order_status_res[0]["OrderStatus"]
            except Exception as e:
                order_status = None
                logger.error("Exception in send_exit_orders: {e}")

            if order_status == "Filled":
                # Get the OrderPreset Object
                order_preset_obj = variables.map_unique_id_to_order_preset[unique_id]
                # Get Values
                entry_qty = order_preset_obj.entry_quantity
                tp1_price = order_preset_obj.tp1_price
                tp2_price = order_preset_obj.tp2_price
                sl1_price = order_preset_obj.sl1_price
                sl2_price = order_preset_obj.sl2_price
                contract = order_preset_obj.contract

                # Create Orders
                orders = OrderGenerator.get_orders_for_strategy(
                    entry_qty=entry_qty,
                    tp1=tp1_price,
                    sl1=sl1_price,
                    tp2=tp2_price,
                    sl2=sl2_price,
                )

                # Send Orders
                for order in orders:
                    logger.info(f"UID: {unique_id} Sending Exit Order: {order}")
                    MonitorOrderPreset.send_order_to_tws(unique_id, contract, order)

                time.sleep(0.2)

                # Log
                logger.info(f"UID: {unique_id} All Exit orders sent to tws")

                # Update the status in the database and order preset object
                MonitorOrderPreset.update_order_preset_state(
                    unique_id, "Live", entry_qty, flag_exit_order_sent=True
                )

                time.sleep(0.05)

                # Pop the entry order id from the list
                strategy_variables.list_of_unique_ids_for_which_entry_order_is_pending.pop(
                    index
                )
            elif order_status in ["Cancelled", "Rejected", "Inactive"]:
                symbol = variables.map_unique_id_to_order_preset[unique_id].ticker

                # Update the status in the database and order preset object
                MonitorOrderPreset.update_order_preset_state(
                    unique_id,
                    "Failed",
                    flag_entry_order_sent=False,
                    flag_exit_order_sent=False,
                )

                # Reduce the count of the ticker
                strategy_variables.map_symbol_to_sent_completed_execution[symbol] -= 1

                # Pop the entry order id from the list
                strategy_variables.list_of_unique_ids_for_which_entry_order_is_pending.pop(
                    index
                )

    @staticmethod
    def update_order_preset_state(
        unique_id,
        status,
        calculated_entry_qty=None,
        risk_dollar=None,
        nlv=None,
        flag_entry_order_sent=None,
        entry_order_id=None,
        flag_exit_order_sent=None,
        failure_reason=None,
    ):
        # Update the Database
        values_dict = {
            "Status": status,
        }

        if calculated_entry_qty is not None:
            values_dict["EntryQuantity"] = calculated_entry_qty
        if risk_dollar is not None:
            values_dict["RiskDollar"] = risk_dollar
        if nlv is not None:
            values_dict["NetLiquidationValue"] = nlv
        if flag_entry_order_sent is not None:
            values_dict["FlagEntryOrderSent"] = 1 if flag_entry_order_sent else 0
        if flag_exit_order_sent is not None:
            values_dict["FlagExitOrderSent"] = 1 if flag_exit_order_sent else 0

        if entry_order_id is not None:
            values_dict["EntryOrderID"] = entry_order_id

        if failure_reason is not None:
            values_dict["FailureReason"] = failure_reason

        where_clause = f"WHERE UniqueID = {unique_id}"
        SqlQueries.update_preset_order(values_dict, where_clause)

        # Get the OrderPreset Object
        order_preset_obj = variables.map_unique_id_to_order_preset[unique_id]

        # Update the OrderPreset Object
        order_preset_obj.change_value("status", status)
        if calculated_entry_qty is not None:
            order_preset_obj.change_value("entry_quantity", calculated_entry_qty)
        if risk_dollar is not None:
            order_preset_obj.change_value("risk_dollar", risk_dollar)
        if nlv is not None:
            order_preset_obj.change_value("net_liquidation_value", nlv)
        if flag_entry_order_sent is not None:
            order_preset_obj.change_value(
                "flag_entry_order_sent", flag_entry_order_sent
            )
        if flag_exit_order_sent is not None:
            order_preset_obj.change_value("flag_exit_order_sent", flag_exit_order_sent)
        if entry_order_id is not None:
            order_preset_obj.change_value("entry_order_id", entry_order_id)
        if failure_reason is not None:
            order_preset_obj.change_value("failure_reason", failure_reason)
