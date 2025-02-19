import re
import math
from com.variables import *
from com.hv_calculation import *
from com import leg_identifier
from com.calc_weighted_change import *


# method to get leg-to-combo highest price ratio
def highest_price_of_leg_div_by_highest_price_of_combination(
    unique_id, combo_obj, all_leg_dataframe_for_combination
):
    # Buy legs and Sell legs
    buy_legs = combo_obj.buy_legs
    sell_legs = combo_obj.sell_legs
    all_legs = buy_legs + sell_legs

    # Dict for multiplication factor based on leg obj action
    dict_action_multiplying_factor = {"BUY": 1, "SELL": -1}

    try:
        # Get highest closing price for combination since open of day
        highest_value_of_combination_since_open_of_day = (
            all_leg_dataframe_for_combination["Combination Close"].max()
        )
    except Exception as e:
        # set to N/A
        highest_value_of_combination_since_open_of_day = "N/A"

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Inside finding highest closing price for combination since open of day, error is {e}"
            )

    # Initialize list to store highest_price_of_leg_div_by_highest_price_of_combination values for each leg
    max_closing_prices_for_each_leg_div_by_max_closing_prices_for_combination_list = {}

    # Check if highest price is not 0
    if highest_value_of_combination_since_open_of_day != 0:
        # Iterate over all legs object
        for leg_number, leg_obj in enumerate(all_legs, start=1):
            try:
                # Finding highest value of leg and dividing it by highest values of combination
                highest_price_for_leg_since_day_opened = (
                    all_leg_dataframe_for_combination[f"Close {leg_number}"].max()
                    * leg_obj.quantity
                    * leg_obj.multiplier
                    * dict_action_multiplying_factor[leg_obj.action]
                )

                # check if values are valid
                if highest_value_of_combination_since_open_of_day not in [
                    0,
                    "N/A",
                    None,
                ]:
                    # calculate ratio of leg -to-combo value
                    max_closing_prices_for_each_leg_div_by_max_closing_prices_for_combination_list[
                        f"Highest Value of Leg {leg_number}"
                    ] = round(
                        highest_price_for_leg_since_day_opened
                        / highest_value_of_combination_since_open_of_day,
                        4,
                    )

            except Exception as e:
                # append N/A if exception happened
                max_closing_prices_for_each_leg_div_by_max_closing_prices_for_combination_list[
                    f"Highest Value of Leg {leg_number}"
                ] = "N/A"

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Inside finding highest closing price for leg divided by highest closing price for combination since open of day, error is {e}"
                    )
    else:
        # Iterate over all legs object
        for leg_number, leg_obj in enumerate(all_legs, start=1):
            max_closing_prices_for_each_leg_div_by_max_closing_prices_for_combination_list[
                f"Highest Value of Leg {leg_number}"
            ] = "N/A"

    return (
        max_closing_prices_for_each_leg_div_by_max_closing_prices_for_combination_list
    )


# Method to calculate leg-to-combo ratio of change in price
def change_in_price_for_leg_div_by_change_in_price_for_combination(
    unique_id, combo_obj, all_leg_dataframe_for_combination
):
    # Since open of day

    # Buy legs and Sell legs
    buy_legs = combo_obj.buy_legs
    sell_legs = combo_obj.sell_legs
    all_legs = buy_legs + sell_legs

    # mapping of side multiplier
    dict_action_multiplying_factor = {"BUY": 1, "SELL": -1}

    # Initialize list to store highest_price_of_leg_div_by_highest_price_of_combination values for each leg
    change_in_prices_for_each_leg_div_by_change_in_prices_for_combination_list = {}

    # Getting day open values and most recent values in lookback period
    day_start_value_for_combination_close_prices = all_leg_dataframe_for_combination[
        "Combination Close"
    ].head(1)
    most_recent_value_for_combination_close_prices = all_leg_dataframe_for_combination[
        "Combination Close"
    ].tail(1)

    # Init
    current_day_open_for_legs_list = []

    # Iterate over all legs object
    for leg_number, leg_obj in enumerate(all_legs):
        try:
            # Getting day open values and most recent values in lookback period
            day_start_value_for_leg_close_price = float(
                all_leg_dataframe_for_combination[f"Close {leg_number + 1}"].head(1)
            )

            # append day start value of leg to list
            current_day_open_for_legs_list.append(day_start_value_for_leg_close_price)

        except Exception as e:
            # Set to none
            current_day_open_for_legs_list = "N/A"

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Error inside getting day open of legs for cas pop up column, is {e}"
                )

    # Calculate change in price for combination prices since open
    if variables.flag_weighted_change_in_price:
        try:
            # Calculate weighted average
            # print(f"Unique ID: {unique_id} Change From Open")
            change_in_price_for_combination_value = calc_weighted_change_legs_based(
                combo_obj, current_day_open_for_legs_list
            )

        except Exception as e:
            # Set to N/A
            change_in_price_for_combination_value = "N/A"

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Error inside getting weighted change in price of combo for cas pop up column, is {e}"
                )
    else:
        try:
            # calculate lof formula for change in price
            change_in_price_for_combination_value = math.log(
                abs(most_recent_value_for_combination_close_prices) + 1
            ) * math.copysign(
                1, most_recent_value_for_combination_close_prices
            ) - math.log(
                abs(day_start_value_for_combination_close_prices) + 1
            ) * math.copysign(1, day_start_value_for_combination_close_prices)

        except Exception as e:
            # Set to N/A
            change_in_price_for_combination_value = "N/A"

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Error inside getting change in price of combo for cas pop up column, is {e}"
                )

    # If we have "change_in_price_for_combination_value" calculate the change in price since open for each leg
    if change_in_price_for_combination_value not in [0, "N/A"]:
        # Iterate over all legs object
        for leg_number, leg_obj in enumerate(all_legs):
            try:
                # Getting day open values and most recent values in lookback period
                day_start_value_for_leg_close_price = float(
                    all_leg_dataframe_for_combination[f"Close {leg_number + 1}"].head(1)
                )

                # get bid ask values
                con_id = leg_obj.con_id
                req_id = variables.con_id_to_req_id_dict[con_id]
                bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]

                # get current price for leg
                most_recent_value_for_leg_close_price = (ask + bid) / 2

                # Calculate change in price for leg prices
                if variables.flag_weighted_change_in_price:
                    # Calculate change in price for each leg
                    change_ratio_for_leg_value = [
                        (
                            most_recent_value_for_leg_close_price
                            / day_start_value_for_leg_close_price
                        )
                        - 1
                    ]

                    # Calculate weight for each leg for weighted avrerage
                    weight_for_leg = [
                        day_start_value_for_leg_close_price
                        * leg_obj.quantity
                        * leg_obj.multiplier
                        * dict_action_multiplying_factor[leg_obj.action]
                    ]

                    # Calculate weighted average
                    change_in_prices_for_each_leg_value = np.average(
                        change_ratio_for_leg_value, weights=weight_for_leg
                    )

                else:
                    # Calculate change in price using log function
                    change_in_prices_for_each_leg_value = math.log(
                        abs(most_recent_value_for_leg_close_price) + 1
                    ) * math.copysign(
                        1, most_recent_value_for_leg_close_price
                    ) - math.log(
                        abs(day_start_value_for_leg_close_price) + 1
                    ) * math.copysign(1, day_start_value_for_leg_close_price)

                # check if values are valid
                if change_in_price_for_combination_value not in [0, "N/A", None]:
                    # Add results to dictionary
                    change_in_prices_for_each_leg_div_by_change_in_prices_for_combination_list[
                        f"Change in Price Value of Leg {leg_number + 1}"
                    ] = round(
                        change_in_prices_for_each_leg_value
                        / change_in_price_for_combination_value,
                        4,
                    )

            except Exception as e:
                # Set value to N/A
                change_in_prices_for_each_leg_div_by_change_in_prices_for_combination_list[
                    f"Change in Price Value of Leg {leg_number + 1}"
                ] = "N/A"

                # Print to console
                if variables.flag_debug_mode:
                    print(
                        f"Inside finding change in price for leg divided by change in price for combination since open of day, error is {e}"
                    )

    else:
        # if we not able to calculate the change_in_price for Combo set every value to "N/A"
        # Iterate over all legs object
        for leg_number, leg_obj in enumerate(all_legs):
            change_in_prices_for_each_leg_div_by_change_in_prices_for_combination_list[
                f"Change in Price Value of Leg {leg_number + 1}"
            ] = "N/A"

    return change_in_prices_for_each_leg_div_by_change_in_prices_for_combination_list


# Method get leg-to-combo ratio of HV value
def hv_of_leg_since_open_div_by_hv_of_combination_since_open(
    unique_id, combo_obj, all_leg_dataframe_for_combination
):
    # Initializing dictionary to store HV values for legs
    hv_value_for_leg = {}

    # Init
    hv_of_leg_since_open_div_by_hv_of_combination_since_open_value = {}

    # Defining avg_price_combo to none
    avg_price_combo = None

    # Buy legs and Sell legs
    buy_legs = combo_obj.buy_legs
    sell_legs = combo_obj.sell_legs
    all_legs = buy_legs + sell_legs

    try:
        # We will need the average price of Combo when the H. V. Method selected is "NATR"
        if variables.hv_method.name == "NATR":
            # avg price for combo
            avg_price_combo = (
                variables.unique_id_to_prices_dict[unique_id]["BUY"]
                + variables.unique_id_to_prices_dict[unique_id]["SELL"]
            ) / 2

        # Get dataframe for combination intraday prices
        combination_dataframe = all_leg_dataframe_for_combination[
            ["Time", "Combination Open", "Combination Close"]
        ].copy()

        # Calculate HV for combination using the intraday prices data.
        hv_value_for_combination = calculate_hv(
            unique_id,
            variables.hv_method,
            combination_dataframe,
            avg_price_combo,
            flag_is_intraday=True,
            leg_number=None,
            flag_combination=True,
        )

    except Exception as e:
        avg_price_combo = "N/A"
        hv_value_for_combination = "N/A"

        # Print to console
        if variables.flag_debug_mode:
            print(
                f" Calculating HV for combination with intraday values inside 'hv_of_leg_since_open_div_by_hv_of_combination_since_open', error is {e}"
            )

    # Iterate over all legs object
    for leg_number, leg_obj in enumerate(all_legs, start=1):
        # Init
        avg_price_for_leg = None

        try:
            # check if method is NATR
            if variables.hv_method.name == "NATR":
                # Get con-id of leg
                con_id = leg_obj.con_id

                # Get quantity of leg
                quantity = int(leg_obj.quantity)

                # Multiplier/Lot size
                if leg_obj.multiplier is None:
                    multiplier = 1
                else:
                    multiplier = int(leg_obj.multiplier)

                try:
                    # Map to dictionary of bid and ask prices
                    req_id = variables.con_id_to_req_id_dict[con_id]
                    bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]

                    # Calculate bid and ask prices for leg
                    bid, ask = bid * quantity * multiplier, ask * quantity * multiplier

                    # Get average price for leg
                    avg_price_for_leg = (ask + bid) / 2

                except Exception as e:
                    # Set to N/A
                    avg_price_for_leg = "N/A"

                    # Print to console:
                    if variables.flag_debug_mode:
                        print(f"Exception in Price {e}")

                    # Set value to N/A
                    hv_value_for_leg[f"HV {leg_number}"] = "N/A"

                    continue

            # Get dataframe for each leg
            leg_dataframe = all_leg_dataframe_for_combination[
                ["Time", f"Open {leg_number}", f"Close {leg_number}"]
            ].copy()

            # Calculating HV for each leg
            hv_value_for_leg[f"HV {leg_number}"] = calculate_hv(
                unique_id,
                variables.hv_method,
                leg_dataframe,
                avg_price_for_leg,
                flag_is_intraday=True,
                leg_number=leg_number,
                flag_combination=False,
            )

            # check if values are valid
            if hv_value_for_combination not in [0, "N/A", None]:
                # Calculating HV of leg divided by hv of combination for each leg
                hv_of_leg_since_open_div_by_hv_of_combination_since_open_value[
                    f"HV {leg_number}"
                ] = round(
                    hv_value_for_leg[f"HV {leg_number}"] / hv_value_for_combination, 4
                )

        except Exception as e:
            # Assigning 'N/A' value for hv of leg
            hv_value_for_leg[f"HV {leg_number}"] = "N/A"
            if variables.flag_debug_mode:
                print(f"Inside calculating hv for legs of combination , error is {e}")

    return hv_of_leg_since_open_div_by_hv_of_combination_since_open_value
