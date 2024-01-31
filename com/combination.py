"""
Created on 15-Mar-2023

@author: Karan
"""
from com.leg import *
from com.variables import *

# Create class
class Combination(object):

    # Initial function of class
    def __init__(self, unique_id, leg_obj_list):

        # Init
        self.unique_id = int(unique_id)
        self.buy_legs = []
        self.sell_legs = []

        # Iterate leg objects
        for leg_obj in leg_obj_list:

            # if action if buy
            if leg_obj.action == "BUY":
                self.buy_legs.append(leg_obj)
            # If action is sell
            elif leg_obj.action == "SELL":
                self.sell_legs.append(leg_obj)
            else:

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Unique ID = {unique_id}, Wrong Value for BUY/SELL {leg_obj.action=}"
                    )

    # get str value
    def __str__(self):

        # Init
        buy_legs_str = "\n\t".join([str(leg) for leg in self.buy_legs])
        sell_legs_str = "\n\t".join([str(leg) for leg in self.sell_legs])

        # Return str
        return f"Combination(unique_id={self.unique_id},\nBUY LEGS:\n\t{buy_legs_str}\nSELL LEGS:\n\t{sell_legs_str})"


# Informative String for combination Object, used in Screen Gui, as well as in Price Chart
def make_informative_combo_string(combination_obj, need_legs_desc=False):

    # Ticker 1 (Sec Type 1: Expiry 1 C/P Strike 1) +/- Qty 1,
    # Tickers Informative string
    combo_desc_string = ""

    # All Legs
    if need_legs_desc == False:
        all_leg_objs = combination_obj.buy_legs + combination_obj.sell_legs
    else:
        all_leg_objs = combination_obj  # (it will be a list of legs)

    # Processing Leg Obj and appending to combo_desc_string
    for leg_no, leg_obj in enumerate(all_leg_objs):

        # Symbol and SecType
        combo_desc_string += f"{leg_obj.symbol} ({leg_obj.sec_type}"

        # Expiry Date, Right, Strike
        if leg_obj.sec_type in ["FOP", "OPT"]:
            combo_desc_string += (
                f" {leg_obj.expiry_date} {leg_obj.right[0]} {leg_obj.strike_price}"
            )
        # if leg is FUT
        elif leg_obj.sec_type == "FUT":
            combo_desc_string += f" {leg_obj.expiry_date}"

        # Buy/Sell +1 or -1
        if leg_obj.action == "BUY":

            # check if it is last leg
            if leg_no == len(all_leg_objs) - 1:
                combo_desc_string += f") +{leg_obj.quantity}"
            else:
                combo_desc_string += f") +{leg_obj.quantity}, "
        else:
            # check if it is last leg
            if leg_no == len(all_leg_objs) - 1:
                combo_desc_string += f") -{leg_obj.quantity}"
            else:
                combo_desc_string += f") -{leg_obj.quantity}, "

    return combo_desc_string


# It is used to show user the combination details in combination tab of screen GUI
def get_combination_details_list_for_combination_tab_gui(
    unique_id, cas_condition=False
):

    try:

        # If Incremental legs are needed
        if cas_condition:

            # Get CAS Legs Combo Object
            combo_obj = variables.cas_unique_id_to_combo_obj[unique_id]
        else:

            # Get Active Combo Object
            combo_obj = variables.unique_id_to_combo_obj[unique_id]

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print("Error Combo not found for displaying details", e)

        # Show error pop up
        error_title = "Error Combo not found"
        error_string = f"Unable to find the combo."
        variables.screen.display_error_popup(error_title, error_string)

        return (None, None)

    # Column names, to show inside Combination details screen GUI
    leg_columns_for_combo_detail_gui = variables.leg_columns_combo_detail_gui

    # List of tuple (for each row in combination details)
    leg_data_tuple_list = []

    # All Legs in combination
    buy_legs = combo_obj.buy_legs
    sell_legs = combo_obj.sell_legs
    all_legs = buy_legs + sell_legs

    # Processing legs and getting data for row.
    for leg_obj in all_legs:

        # Init
        action = leg_obj.action
        symbol = leg_obj.symbol
        sec_type = leg_obj.sec_type
        exchange = leg_obj.exchange
        currency = leg_obj.currency
        quantity = leg_obj.quantity
        expiry_date = leg_obj.expiry_date
        strike_price = leg_obj.strike_price
        right = leg_obj.right
        multiplier = leg_obj.multiplier
        con_id = leg_obj.con_id
        primary_exchange = leg_obj.primary_exchange
        trading_class = leg_obj.trading_class

        # append values to list
        leg_data_tuple_list.append(
            (
                action,
                symbol,
                sec_type,
                exchange,
                currency,
                quantity,
                expiry_date,
                strike_price,
                right,
                multiplier,
                con_id,
                primary_exchange,
                trading_class,
            )
        )

    return leg_columns_for_combo_detail_gui, leg_data_tuple_list
