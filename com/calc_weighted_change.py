import pandas as pd
from com.variables import *


# Method to get last day close price for each leg
def get_last_day_close_for_each_leg(combo_daily_open_close_df, combo_obj):
    # Init
    close_price_for_legs_list = []

    # Buy legs and Sell legs
    buy_legs = combo_obj.buy_legs
    sell_legs = combo_obj.sell_legs
    all_legs = buy_legs + sell_legs

    try:
        # Create a new column 'Date' that contains only the date part of the 'Time' column
        combo_daily_open_close_df["Date"] = pd.to_datetime(
            combo_daily_open_close_df["Time"]
        ).dt.date

        # Get the maximum date in the 'Date' column
        max_date = combo_daily_open_close_df["Date"].max()

        # Get the second to last date in the 'Date' column
        second_last_date = combo_daily_open_close_df[
            combo_daily_open_close_df["Date"] < max_date
        ]["Date"].max()

        # Get the row corresponding to the second to last date
        second_last_row = combo_daily_open_close_df[
            combo_daily_open_close_df["Date"] == second_last_date
        ].iloc[-1]

        # Get all columns that start with 'Close'
        close_cols = [
            col for col in combo_daily_open_close_df.columns if col.startswith("Close")
        ]

        # Get the last day close price for all underlying
        legs_last_day_close = list(second_last_row[close_cols])

    except Exception as e:
        # Print to console
        if variables.flag_debug_mode:
            print(f"Error inside getting last day close price, is {e}")

        return "N/A"

    # Iterate two values from two list to get last close price for each leg
    for _, (leg_obj, leg_close) in enumerate(zip(all_legs, legs_last_day_close)):
        # Last Close
        try:
            # Confirm This
            close_price = float(leg_close)

        except Exception as e:
            # Print to console
            if variables.flag_debug_mode:
                print("Unable to get Combo close")

            # Set to none
            close_price = None

        # Append close value to list
        close_price_for_legs_list.append(close_price)

    # check if a number of legs is equal to number of close prices system got
    if len(close_price_for_legs_list) != len(all_legs):
        # set to none
        close_price_for_legs_list = "N/A"

    return close_price_for_legs_list


# Method to get price for each leg at specified timestamp
def get_values_for_each_leg(
    combo_daily_open_close_df,
    combo_obj,
    combo_price_type_highest_or_lowest_or_current=None,
):
    # Init
    values_for_legs_list = []

    # Buy legs and Sell legs
    buy_legs = combo_obj.buy_legs
    sell_legs = combo_obj.sell_legs
    all_legs = buy_legs + sell_legs

    # When value for price_type_highest_or_lowest_or_current is set none then get day open values for legs
    if combo_price_type_highest_or_lowest_or_current == None:
        # Get the row corresponding to the first row
        df_row = combo_daily_open_close_df.iloc[0]

    # When value for price_type_highest_or_lowest_or_current is set none then get current values for legs
    elif combo_price_type_highest_or_lowest_or_current == "Current":
        # Get the row corresponding to the first row
        df_row = combo_daily_open_close_df.iloc[-1]

    # When value for price_type_highest_or_lowest_or_current is set "Highest" then get day values for legs at timestamp of highest combo price
    elif combo_price_type_highest_or_lowest_or_current == "Highest":
        # Get the index of the row where the highest price of column 'Combination Close' occurred
        index_of_highest_price = combo_daily_open_close_df["Combination Close"].idxmax()

        # Get the row corresponding to the row index
        df_row = combo_daily_open_close_df.iloc[index_of_highest_price]

    # When value for price_type_highest_or_lowest_or_current is set "Lowest" then get day values for legs at timestamp of lowest combo price
    elif combo_price_type_highest_or_lowest_or_current == "Lowest":
        # Get the index of the row where the lowest price of column 'Combination Close' occurred
        index_of_lowest_price = combo_daily_open_close_df["Combination Close"].idxmin()

        # Get the row corresponding to the row index
        df_row = combo_daily_open_close_df.iloc[index_of_lowest_price]

    # Get all columns that start with 'Close'
    close_cols = [
        col for col in combo_daily_open_close_df.columns if col.startswith("Close")
    ]

    # Get the last day close price for all underlying
    legs_current_day_values = list(df_row[close_cols])

    # Iterate over values of legs list and current day price list
    for _, (leg_obj, leg_open) in enumerate(zip(all_legs, legs_current_day_values)):
        # Last Close
        try:
            # Confirm This
            price_for_leg = float(leg_open)

        except Exception as e:
            # Print to console
            if variables.flag_debug_mode:
                print("Unable to get current day open for the leg")
            price_for_leg = None

        # Append current price to list
        values_for_legs_list.append(price_for_leg)

    # Validating if current price is available for each leg
    if len(values_for_legs_list) != len(all_legs):
        values_for_legs_list = "N/A"

    return values_for_legs_list


# Calculated weighted average method
def calc_weighted_change_legs_based(
    combo_obj,
    leg_wise_price,
    most_recent_value_for_day_in_lookback=None,
    flag=False,
    unique_id=None,
):
    # Buy legs and Sell legs
    buy_legs = combo_obj.buy_legs
    sell_legs = combo_obj.sell_legs
    all_legs = buy_legs + sell_legs

    # side multiplier mapping
    dict_action_multiplying_factor = {"BUY": 1, "SELL": -1}

    # Init
    change_in_price_for_all_legs = []
    weights_for_legs = []
    # Not used only for debugging
    temp_current_price = []

    # Processing "Buy" Legs to calculate prices
    for leg_indx, (leg_obj, leg_price) in enumerate(zip(all_legs, leg_wise_price)):
        try:
            # Init
            quantity = int(float(leg_obj.quantity))
            con_id = leg_obj.con_id
            multiplier = int(float(leg_obj.multiplier))
            action = leg_obj.action

            # if most_recent_value_for_day_in_lookback is None
            if most_recent_value_for_day_in_lookback == None:
                # get bid ask value
                req_id = variables.con_id_to_req_id_dict[con_id]
                bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]

                # clcualte current price
                current_price = (ask + bid) / 2

                # Check if unique ID is not none
                if unique_id != None:
                    pass  # print(f"{unique_id=}, {leg_indx=}, {current_price=}")
            else:
                # get current price from most_recent_value_for_day_in_lookback list
                current_price = most_recent_value_for_day_in_lookback[leg_indx]

            # append current price to list
            temp_current_price.append(current_price)

            # calculate change in price for leg
            change_in_price = (current_price / leg_price) - 1

            # Append change in price for leg
            change_in_price_for_all_legs.append(change_in_price)

            # calculate weight for leg
            weight_for_leg = (
                leg_price
                * quantity
                * multiplier
                * dict_action_multiplying_factor[action]
            )

            # Append weight of leg to list
            weights_for_legs.append(weight_for_leg)

        except Exception as e:
            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Error inside upper calculating weighed change leg based  is {e}"
                )
    # if flag:
    #     print([most_recent_value_for_day_in_lookback,leg_wise_price])
    #     print([change_in_price_for_all_legs,weights_for_legs])
    # Print to console
    if variables.flag_debug_mode:
        print(
            f"Unique ID: {combo_obj.unique_id}, Price at T1: {leg_wise_price} Price at T2: {temp_current_price} Weights: {weights_for_legs}"
        )

    try:
        # validate if system has all required change in price and weights
        if len(weights_for_legs) == len(all_legs):
            # Calculate the weighted average
            weighted_change_in_price = np.average(
                change_in_price_for_all_legs, weights=weights_for_legs
            )

        else:
            # Set to N/A
            weighted_change_in_price = "N/A"

    except Exception as e:
        # Set to N/A
        weighted_change_in_price = "N/A"

        # Print to console
        if variables.flag_debug_mode:
            print(f"Error inside calculating weighed change leg based,  is {e}")

    return weighted_change_in_price
