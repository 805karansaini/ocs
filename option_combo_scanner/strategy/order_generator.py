import math

from option_combo_scanner.ibapi.order import Order
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.strategy_variables import (
    StrategyVariables as strategy_variables,
)


class OrderGenerator:
    def __init__(self):
        pass

    @staticmethod
    def create_entry_mkt_order(entry_qty):
        """
        Creates a Market Order
        """
        order_id = variables.app.nextorderId
        variables.app.nextorderId += 1

        # Creating Order
        entry_order = Order()
        entry_order.action = "BUY"
        entry_order.totalQuantity = entry_qty
        entry_order.orderId = order_id
        entry_order.orderRef = ""
        entry_order.orderType = "MKT"
        entry_order.account = variables.account_id
        entry_order.transmit = True
        entry_order.tif = "GTC"

        return entry_order

    @staticmethod
    def create_bracket_order_without_tp2(entry_qty, tp1, sl1, sl2):
        group_1_qty = int(entry_qty / 2)
        group_2_qty = entry_qty - group_1_qty

        group1_tp, group1_sl = OrderGenerator.create_oca_group_order(
            "Group1", 0, group_1_qty, tp1, sl1
        )
        group2_tp, group2_sl = OrderGenerator.create_oca_group_order(
            "Group2", 0, group_2_qty, tp1, sl2
        )

        return [group1_tp, group1_sl, group2_tp, group2_sl]

    @staticmethod
    def create_bracket_order_without_sl2(entry_qty, tp1, sl1, tp2):
        group_1_qty = int(entry_qty / 2)
        group_2_qty = entry_qty - group_1_qty

        group1_tp, group1_sl = OrderGenerator.create_oca_group_order(
            "Group1", 0, group_1_qty, tp1, sl1
        )
        group2_tp, group2_sl = OrderGenerator.create_oca_group_order(
            "Group2", 0, group_2_qty, tp2, sl1
        )

        return [group1_tp, group1_sl, group2_tp, group2_sl]

    @staticmethod
    def create_bracket_order_without_tp2_and_sl2(entry_qty, tp1, sl1):
        group1_tp, group1_sl = OrderGenerator.create_oca_group_order(
            "Group1", 0, entry_qty, tp1, sl1
        )

        return group1_tp, group1_sl

    @staticmethod
    def create_bracket_order_with_tp2_and_sl2(entry_qty, tp1, sl1, tp2, sl2):
        # entry_order = OrderGenerator.create_entry_mkt_order(entry_qty)
        one_fourth_qty = max(math.floor(entry_qty / 4), 1)

        group1_qty, group_2_qty, group3_qty, group4_qty = [
            one_fourth_qty,
            one_fourth_qty,
            one_fourth_qty,
            entry_qty - 3 * one_fourth_qty,
        ]

        group1_tp, group1_sl = OrderGenerator.create_oca_group_order(
            "Group1", 0, group1_qty, tp1, sl1
        )
        group2_tp, group2_sl = OrderGenerator.create_oca_group_order(
            "Group2", 0, group_2_qty, tp1, sl2
        )
        group3_tp, group3_sl = OrderGenerator.create_oca_group_order(
            "Group3", 0, group3_qty, tp2, sl1
        )
        group4_tp, group4_sl = OrderGenerator.create_oca_group_order(
            "Group4", 0, group4_qty, tp2, sl2
        )

        return [
            group1_tp,
            group1_sl,
            group2_tp,
            group2_sl,
            group3_tp,
            group3_sl,
            group4_tp,
            group4_sl,
        ]

    @staticmethod
    def create_oca_group_order(oca_str, oca_type, quantity, tp, sl):
        order_id = variables.app.nextorderId
        variables.app.nextorderId += 2

        # Make the String for OCA Group[Unique]
        oca_str = oca_str + " " + str(order_id)

        # Bracket Order1: TP1a and SL1a
        take_profit = Order()
        take_profit.orderId = order_id
        take_profit.action = "SELL"
        take_profit.orderType = "LMT"
        take_profit.totalQuantity = quantity
        take_profit.lmtPrice = tp
        take_profit.account = variables.account_id
        take_profit.ocaGroup = oca_str
        take_profit.ocaType = oca_type
        take_profit.transmit = True
        take_profit.tif = "GTC"

        stop_loss = Order()
        stop_loss.orderId = order_id + 1
        stop_loss.action = "SELL"
        stop_loss.orderType = "STP"
        stop_loss.auxPrice = sl
        stop_loss.totalQuantity = quantity
        stop_loss.account = variables.account_id
        stop_loss.ocaGroup = oca_str
        stop_loss.ocaType = oca_type
        stop_loss.transmit = True
        stop_loss.tif = "GTC"

        return [take_profit, stop_loss]

    @staticmethod
    def get_entry_order_for_strategy(entry_qty):
        return OrderGenerator.create_entry_mkt_order(entry_qty)

    @staticmethod
    def get_orders_for_strategy(entry_qty, tp1, sl1, tp2, sl2):
        if (tp2 != None and sl2 != None) and (entry_qty > 3):
            return OrderGenerator.create_bracket_order_with_tp2_and_sl2(
                entry_qty, tp1, sl1, tp2, sl2
            )
        elif tp2 == None and sl2 != None and entry_qty > 1:
            return OrderGenerator.create_bracket_order_without_tp2(
                entry_qty, tp1, sl1, sl2
            )
        elif sl2 == None and tp2 != None and entry_qty > 1:
            return OrderGenerator.create_bracket_order_without_sl2(
                entry_qty, tp1, sl1, tp2
            )
        else:
            return OrderGenerator.create_bracket_order_without_tp2_and_sl2(
                entry_qty, tp1, sl1
            )
