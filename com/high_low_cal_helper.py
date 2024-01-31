"""
Created on 12-Jul-2023

@author: Ashish
"""

import enum

import pandas as pd

from com import *
from com.prices import *
from com.variables import variables
from com.hv_calculation import *
from com.significant_levels_support_resistance import *
import numpy as np
from com.cas_pop_up_window_related_columns import *
from com.calc_weighted_change import *
from com.combination_helper import create_combination


# Adjust the parameter
# fetch data
# compute the value
# return save and update in gui
# (remove extra old code)
# ###
# Update the table in gui in correct order. resturc df.

# Method to fetch historical data
def get_historical_data_for_price_based_relative_indicators(
    cas_coinds_for_fetching_historical_data,
    duration_size,
    bar_size,
    flag_both_bid_ask=False,
):

    # Map of [conid][action] = req_id
    map_conid_action_to_req_id = {}

    # List of all request ids
    req_id_list = []

    # Iterae for every combo
    for conid, sub_info_dict in cas_coinds_for_fetching_historical_data.items():
        contract = variables.map_con_id_to_contract[conid]

        # Create dict with conid as key
        if conid not in map_conid_action_to_req_id:
            map_conid_action_to_req_id[conid] = {}

        # Iterate actions an sub values
        for action, sub_values in sub_info_dict.items():

            if not flag_both_bid_ask:

                # Create dict with conid as key
                if action not in map_conid_action_to_req_id[conid]:
                    map_conid_action_to_req_id[conid][action] = None

                # Getting req_id
                reqId = variables.cas_app.nextorderId
                variables.cas_app.nextorderId += 1

                # Historical Data to ReqId
                map_conid_action_to_req_id[conid][action] = reqId

                # append reqid it to the list
                req_id_list.append(reqId)

                if action == "BUY":
                    what_to_show = "ASK"
                else:
                    what_to_show = "BID"

                # Get the historical data
                request_historical_price_data_for_contract(
                    contract,
                    bar_size,
                    duration_size,
                    what_to_show,
                    req_id=reqId,
                    cas_app=True,
                )

            else:

                # Init
                map_conid_action_to_req_id[conid]["BUY"] = None
                map_conid_action_to_req_id[conid]["SELL"] = None

                # Getting req_id
                reqId = variables.cas_app.nextorderId
                variables.cas_app.nextorderId += 1

                # Historical Data to ReqId
                map_conid_action_to_req_id[conid]["BUY"] = reqId

                # append reqid it to the list
                req_id_list.append(reqId)

                # Init
                what_to_show = "ASK"

                # Get the historical data
                request_historical_price_data_for_contract(
                    contract,
                    bar_size,
                    duration_size,
                    what_to_show,
                    req_id=reqId,
                    cas_app=True,
                )

                # Getting req_id
                reqId = variables.cas_app.nextorderId
                variables.cas_app.nextorderId += 1

                # Historical Data to ReqId
                map_conid_action_to_req_id[conid]["SELL"] = reqId

                # append reqid it to the list
                req_id_list.append(reqId)

                what_to_show = "BID"

                # Get the historical data
                request_historical_price_data_for_contract(
                    contract,
                    bar_size,
                    duration_size,
                    what_to_show,
                    req_id=reqId,
                    cas_app=True,
                )

    # Init
    counter = 0

    # Wait for data
    while variables.cas_wait_time_for_historical_data > (
        counter * variables.sleep_time_waiting_for_tws_response
    ):

        """dict_mkt_end = variables.req_mkt_data_end
        dicterr_msg = variables.req_error

        merged_dict = {}

        for key in set(dict_mkt_end.keys()) | set(dicterr_msg.keys()):
            if key in dict_mkt_end and key in dicterr_msg:
                merged_dict[key] = dict_mkt_end[key] or dicterr_msg[key]
            elif key in dict_mkt_end:
                merged_dict[key] = dict_mkt_end[key]
            else:
                merged_dict[key] = dicterr_msg[key]

        # If reqHistorical Data ended for all the reqId
        if all([merged_dict[req_id] for req_id in req_id_list]):
            break"""
        # Check if data is arrived
        if all(
            [
                variables.req_mkt_data_end[req_id] or variables.req_error[req_id]
                for req_id in req_id_list
            ]
        ):
            break

        # Sleep for sleep_time_waiting_for_tws_response
        time.sleep(variables.sleep_time_waiting_for_tws_response)

        # Increase Counter
        counter += 1

    return map_conid_action_to_req_id

# Method to get merged df to get combo price from leg prices
def merge_dataframe_inner_join_with_combo_price_calculation(combo_obj, all_data_frames):

    # All legs in combo
    all_legs = combo_obj.buy_legs + combo_obj.sell_legs

    # 1st Data Frame
    merged_df = all_data_frames[0]

    # Merging all data frames such that Time is available in all data frames
    for i, df_ith in enumerate(all_data_frames[1:]):
        merged_df = pd.merge(
            merged_df, df_ith, on="Time", how="inner", suffixes=(f"", f" {i+1}")
        )

    # Dropping nan values, if any
    merged_df = merged_df.dropna()

    # Creating Columns for merged dataframe
    merged_df_columns = ["Time"]

    # Open and Close with leg
    for i in range(len(all_data_frames)):
        merged_df_columns.append(f"Open {i+1}")
        merged_df_columns.append(f"Close {i+1}")
        merged_df_columns.append(f"Volume {i+1}")

    # Setting columns in merged_df
    merged_df.columns = merged_df_columns

    # Multipling Factors to calculate the historical price of combination
    factors = []

    # Calculating Factor ( mulitplier * leg_qty * (+1 if buy else -1) )
    for leg_obj in all_legs:

        # Init
        quantity = int(leg_obj.quantity)
        multiplier = leg_obj.multiplier

        # Check if multiplier is invalid
        if (multiplier == None) or (multiplier == "None"):
            multiplier = 1
        else:
            # Convert to integer
            multiplier = int(multiplier)

        # Check if action is buy
        if leg_obj.action == "BUY":
            factors.append(quantity * multiplier)
        else:
            factors.append(-1 * quantity * multiplier)

    # Calculating combination Open
    merged_df["Combination Open"] = merged_df.apply(
        lambda row: formula_to_calculate_price_for_historical_data(
            row, "Open", all_data_frames, factors
        ),
        axis=1,
    )

    # Calculating combination close
    merged_df["Combination Close"] = merged_df.apply(
        lambda row: formula_to_calculate_price_for_historical_data(
            row, "Close", all_data_frames, factors
        ),
        axis=1,
    )

    return merged_df

# Method to merge dataframe to get combination volume
def merge_dataframe_inner_join_with_bid_ask_calculation(
    combo_obj, ask_data_frames, bid_data_frames
):
    # All legs in combo
    all_legs = combo_obj.buy_legs + combo_obj.sell_legs

    # get first df
    first_df = ask_data_frames[0].drop(["Volume"], axis=1)

    # 1st Data Frame
    merged_df = first_df

    # get megerd df
    merged_df = merged_df.drop(["Open", "Close"], axis=1)

    # Merging all data frames such that Time is available in all data frames
    for i, (df_ith, df_ith_bid) in enumerate(
        zip(ask_data_frames, bid_data_frames), start=0
    ):

        # Drop columns
        df_ith = df_ith.drop(["Volume"], axis=1)
        df_ith_bid = df_ith_bid.drop(["Volume"], axis=1)

        # Merge df
        merged_df = pd.merge(
            merged_df, df_ith, on="Time", how="inner", suffixes=(f"", f" Ask {i + 1}")
        )

        # Merge dataframe
        merged_df = pd.merge(
            merged_df,
            df_ith_bid,
            on="Time",
            how="inner",
            suffixes=(f"", f" Bid {i + 1}"),
        )

    # Merging all data frames such that Time is available in all data frames
    """for i, df_ith in enumerate(bid_data_frames):

        df_ith = df_ith.drop(['Volume'], axis=1)

        merged_df = pd.merge(
            merged_df, df_ith, on="Time", how="inner", suffixes=(f"", f" Bid {i + 1}")
        )"""
    # print(merged_df.head().to_string())
    # Dropping nan values, if any
    merged_df = merged_df.dropna()

    # Creating Columns for merged dataframe
    merged_df_columns = ["Time"]

    # Open and Close with leg
    for i in range(len(ask_data_frames)):
        merged_df_columns.append(f"Open Ask {i + 1}")
        merged_df_columns.append(f"Close Ask {i + 1}")
        merged_df_columns.append(f"Open Bid {i + 1}")
        merged_df_columns.append(f"Close Bid {i + 1}")

    # Setting columns in merged_df
    merged_df.columns = merged_df_columns

    # Multipling Factors to calculate the historical price of combination
    factors = []

    # Calculating Factor ( mulitplier * leg_qty * (+1 if buy else -1) )
    for leg_obj in all_legs:
        quantity = int(leg_obj.quantity)
        multiplier = leg_obj.multiplier

        # Check if multiplier value is not valid
        if (multiplier == None) or (multiplier == "None"):
            multiplier = 1
        else:
            multiplier = int(multiplier)

        # Check if action is BUY
        if leg_obj.action == "BUY":
            factors.append(quantity * multiplier)
        else:
            factors.append(-1 * quantity * multiplier)

    # Calculating combination Open
    merged_df["Combination Ask"] = merged_df.apply(
        lambda row: formula_to_calculate_price_for_historical_data(
            row, "Close Ask", bid_data_frames, factors
        ),
        axis=1,
    )

    # Calculating combination close
    merged_df["Combination Bid"] = merged_df.apply(
        lambda row: formula_to_calculate_price_for_historical_data(
            row, "Close Bid", ask_data_frames, factors
        ),
        axis=1,
    )

    return merged_df

# Method to calculate average of absolute difference over lookback period
def calculate_avg_of_abs_change_in_price_for_the_same_time_period(
    unique_id,
    lookback_period_dataframe,
    date_time_start,
    date_time_close,
    flag_last_n_minute_field=False,
    local_unique_id_to_combo_obj=None
):

    # Get combo obj
    try:

        if local_unique_id_to_combo_obj is None:
            local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

        combo_obj = local_unique_id_to_combo_obj[unique_id]
    except Exception as e:
        combo_obj = "N/A"
        if variables.flag_debug_mode:
            print(
                f"Error inside calculating average abs change in prices for lookback period, is {e}"
            )

    # Convert the 'Time' column to datetime type if it's not already
    lookback_period_dataframe["Time"] = pd.to_datetime(
        lookback_period_dataframe["Time"]
    )

    # Filter the rows where the time is between start and end time
    filtered_historical_data_dataframe = lookback_period_dataframe[
        (
            lookback_period_dataframe["Time"].dt.time
            >= pd.to_datetime(date_time_start).time()
        )
        & (
            lookback_period_dataframe["Time"].dt.time
            <= pd.to_datetime(date_time_close).time()
        )
    ].reset_index(drop=True)
    # All dates
    all_date_values = lookback_period_dataframe["Time"].dt.date.unique()

    # Calculate ATR for open and close price data for particular time on each lookback day
    calculated_change_in_for_look_back_days = []

    for date_ith in all_date_values:

        # Filtering the dataframe for the 'date_ith'
        date_specific_dataframe_for_change_in_price = (
            filtered_historical_data_dataframe[
                filtered_historical_data_dataframe["Time"].dt.date == date_ith
            ].reset_index(drop=True)
        )

        # Save DF to CSV File (HV) Export data-frame to csv file
        if (variables.flag_store_cas_tab_csv_files) and not flag_last_n_minute_field:

            file_path = rf"{variables.cas_tab_csv_file_path}\Support Resistance And Relative Fields\RelativeChange"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            # Saving CSV
            date_specific_dataframe_for_change_in_price.to_csv(
                rf"{file_path}\{unique_id}_relv_change_{date_ith}.csv", index=False
            )

        # Save DF to CSV File (HV) Export data-frame to csv file
        elif (variables.flag_store_cas_tab_csv_files) and flag_last_n_minute_field:

            file_path = rf"{variables.cas_tab_csv_file_path}\Last N Minutes Fields\RelativeChange"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            # Saving CSV
            date_specific_dataframe_for_change_in_price.to_csv(
                rf"{file_path}\{unique_id}_relv_change_{date_ith}.csv", index=False
            )

        # Getting day open values and most recent values for specific date in lookback period
        most_recent_values_for_day_row = (
            date_specific_dataframe_for_change_in_price.tail(1)
        )
        day_start_values_for_day_row = date_specific_dataframe_for_change_in_price.head(
            1
        )

        # Getting the most recent and the olderst value for each leg. (Oldest is first candle Close, Recent is last candles close)
        day_open_values_for_days_in_lookback = get_values_for_each_leg(
            day_start_values_for_day_row, combo_obj
        )
        most_recent_values_for_days_in_lookback = get_values_for_each_leg(
            most_recent_values_for_day_row, combo_obj
        )

        # Calculating change in price for ith day
        if variables.flag_weighted_change_in_price:
            change_from_open_value = calc_weighted_change_legs_based(
                combo_obj,
                day_open_values_for_days_in_lookback,
                most_recent_values_for_days_in_lookback,
            )

        else:

            # Calcualte log function change in price
            change_from_open_value = math.log(
                abs(most_recent_values_for_day_row["Combination Close"]) + 1
            ) * math.copysign(
                1, most_recent_values_for_day_row["Combination Close"]
            ) - math.log(
                abs(day_start_values_for_day_row["Combination Close"]) + 1
            ) * math.copysign(
                1, day_start_values_for_day_row["Combination Close"]
            )

        # Appending values in list
        calculated_change_in_for_look_back_days.append(abs(change_from_open_value))

    try:

        # Check if list is empty
        if calculated_change_in_for_look_back_days == []:

            avg_of_change_in_prices_over_lookback = "N/A"
        else:

            # Get mean value of values
            avg_of_change_in_prices_over_lookback = np.mean(
                calculated_change_in_for_look_back_days
            )
    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Inside 'calculate_avg_of_abs_change_in_price_for_the_same_time_period', error is {e}"
            )
        avg_of_change_in_prices_over_lookback = "N/A"

    return avg_of_change_in_prices_over_lookback

# Method to Calculate volume magnet indicator
def calculate_volume_magnet_indicators(
    local_unique_id_to_combo_obj, map_conid_action_to_req_id
):

    # Init dict
    local_map_unique_id_to_volume_magnet_fields = {}

    # dict for combo prices
    local_unique_id_to_prices_dict = copy.deepcopy(variables.unique_id_to_prices_dict)

    # Iterate all combos
    for unique_id, combo_obj in local_unique_id_to_combo_obj.items():

        try:

            # Define default values
            local_map_unique_id_to_volume_magnet_fields[unique_id] = {
                "Volume Magnet": "N/A"
            }

            # Get all legs
            buy_legs = combo_obj.buy_legs
            sell_legs = combo_obj.sell_legs
            all_legs = buy_legs + sell_legs

            # list of request_id
            req_id_list = []

            # Merge Data
            for leg in all_legs:
                action = leg.action
                con_id = leg.con_id
                req_id = map_conid_action_to_req_id[con_id][action]
                req_id_list.append(req_id)

            # Process Data,
            all_data_frames = [
                variables.map_req_id_to_historical_data_dataframe[req_id]
                for req_id in req_id_list
            ]

            # Data not found for any leg
            is_data_frame_empty = False

            # If data is not present
            for i, historical_dataframe in enumerate(all_data_frames):
                if (
                    historical_dataframe is None
                    or len(historical_dataframe.index) == 0
                    or historical_dataframe.empty
                ):
                    is_data_frame_empty = True

                    # Print to console
                    if variables.flag_debug_mode:
                        print(f"Empty Data Frame : Unqiue ID {unique_id}")
                    break

            # Check if data frame is empty
            if is_data_frame_empty:

                # Define default values
                local_map_unique_id_to_volume_magnet_fields[unique_id] = {
                    "Volume Magnet": "N/A"
                }

                continue

            # Merging the data frame, inner join on time
            merged_df = merge_dataframe_inner_join_with_combo_price_calculation(
                combo_obj, all_data_frames
            )

            # Save DF to CSV File
            if variables.flag_store_cas_tab_csv_files:

                file_path = rf"{variables.cas_tab_csv_file_path}\Volume Magnet\Prices"
                file_path += rf"\Unique_id_{unique_id}"

                if not os.path.exists(file_path):
                    os.makedirs(file_path)

                merged_df.to_csv(
                    rf"{file_path}\Unique_ID_{unique_id}_Volume_magnet_prices_df.csv",
                    index=False,
                )

            # get df with useful columns
            combination_price_df = merged_df[
                ["Time", "Combination Open", "Combination Close"]
            ]

            # get volume magnet timestamp
            timestamp_for_price = variables.volume_magnet_time_stamp[unique_id]

            # Check if value is valid
            if timestamp_for_price not in ["N/A", None, "None"]:

                # Filter the DataFrame where 'Time' is 'B' and get the 'combination close' value
                volume_timestamp_price = combination_price_df.loc[
                    combination_price_df["Time"] == timestamp_for_price,
                    "Combination Close",
                ].values[0]

            else:

                volume_timestamp_price = "N/A"

            # Make it available in variables
            curretn_combo_price = merged_df["Combination Close"].iloc[-1]

            # Set value to N/A
            volume_magnet = "N/A"

            # Check if values are valid
            if curretn_combo_price not in [
                "N/A",
                None,
                "None",
            ] and volume_timestamp_price not in ["N/A", None, "None"]:

                # Calculate volume magnet
                volume_magnet = curretn_combo_price - volume_timestamp_price

            # Assign value in dict
            local_map_unique_id_to_volume_magnet_fields[unique_id] = {
                "Volume Magnet": volume_magnet
            }

        except Exception as e:

            # Print to console
            if variables.flag_debug_mode:

                print(f"Expection inside getting volumne magnet, Exp:{e}")

    return local_map_unique_id_to_volume_magnet_fields

# Method to calcualte high low price for range order
def calculate_prices_for_range_order(local_unique_id_to_combo_obj,
    map_conid_action_to_req_id,):

    #  Init Dict
    local_map_unique_id_to_price_for_range_order = {}

    # Local copy of live price
    local_unique_id_to_prices_dict = copy.deepcopy(variables.unique_id_to_prices_dict)


    # Iterate all combos
    for unique_id, combo_obj in local_unique_id_to_combo_obj.items():


        # Define default values
        local_map_unique_id_to_price_for_range_order[unique_id] = {
            "Highest Price": "N/A",
            "Lowest Price": "N/A",

        }

        # Get all legs
        buy_legs = combo_obj.buy_legs
        sell_legs = combo_obj.sell_legs
        all_legs = buy_legs + sell_legs

        # list of request_id
        req_id_list = []

        # Merge Data
        for leg in all_legs:
            action = leg.action
            con_id = leg.con_id
            req_id = map_conid_action_to_req_id[con_id][action]
            req_id_list.append(req_id)

        # Process Data,
        all_data_frames = [
            variables.map_req_id_to_historical_data_dataframe[req_id]
            for req_id in req_id_list
        ]




        # Data not found for any leg
        is_data_frame_empty = False

        # If data is not present
        for i, historical_dataframe in enumerate(all_data_frames):
            if (
                    historical_dataframe is None
                    or len(historical_dataframe.index) == 0
                    or historical_dataframe.empty
            ):
                is_data_frame_empty = True
                # Print to console
                if variables.flag_debug_mode:
                    print(f"Empty Data Frame : Unqiue ID {unique_id}")
                break

        # Check if data frame is empty
        if is_data_frame_empty:
            # Define default values
            local_map_unique_id_to_price_for_range_order[unique_id] = {
                "Highest Price": "N/A",
                "Lowest Price": "N/A",

            }

            continue

        # Merging the data frame, inner join on time
        merged_df = merge_dataframe_inner_join_with_combo_price_calculation(
            combo_obj, all_data_frames
        )

        # get max and min value
        highest_value = merged_df['Combination Close'].max()
        lowest_value = merged_df['Combination Close'].min()

        # Define default values
        local_map_unique_id_to_price_for_range_order[unique_id] = {
            "Highest Price": highest_value,
            "Lowest Price": lowest_value,

        }

    return local_map_unique_id_to_price_for_range_order

# Method to calculate price based relative indicator
def calculate_all_the_price_based_relative_indicators(
    local_unique_id_to_combo_obj,
    map_conid_action_to_req_id,
    last_n_minutes_lookback=None,
):

    # Check if last n minutes inout are none
    if last_n_minutes_lookback == None:

        # Init dict
        local_map_unique_id_to_support_resistance_and_relative_fields = {}
        prices_df_dict = {}

    # If input for last n minutes are available
    elif last_n_minutes_lookback != None:

        #  Init Dict
        local_map_unique_id_to_avg_abs_changes_last_n_minutes = {}

    # Local copy of live price
    local_unique_id_to_prices_dict = copy.deepcopy(variables.unique_id_to_prices_dict)

    for unique_id, combo_obj in local_unique_id_to_combo_obj.items():

        # Check if last n minutes inout are none
        if last_n_minutes_lookback == None:

            # Define default values
            local_map_unique_id_to_support_resistance_and_relative_fields[unique_id] = {
                "Resistance": "N/A",
                "Support": "N/A",
                "Resistance Count": "N/A",
                "Support Count": "N/A",
                "Relative ATR": "N/A",
                "Avg of Abs Changes in Prices": "N/A",
                "Relative ATR Derivative": "N/A",
                "Relative ATR on Positive Candles": "N/A",
                "Relative ATR on Negative Candles": "N/A",
                "Price Support Ratio": "N/A",
                "Price Resistance Ratio": "N/A",
                "Relative ATR Lower": "N/A",
                "Relative ATR Higher": "N/A",
            }
            prices_df_dict[unique_id] = {
                "Latest Day": "N/A",
                "Historic Data Except Current Day": "N/A",
            }

        # If input for last n minutes are available
        elif last_n_minutes_lookback != None:

            # Define default values
            local_map_unique_id_to_avg_abs_changes_last_n_minutes[unique_id] = {
                "Relative Change Last N Minutes": "N/A"
            }

        # Res, sup, count, rel chng, rel atr,
        # local_map_unique_id_to_support_resistance_and_relative_fields[unique_id] = {'Resistance': 'N/A', 'Support': 'N/A', 'Resistance Count': 'N/A',
        #                                                                            'Support Count': 'N/A', 'Relative ATR': 'N/A', 'Avg of Abs Changes in Prices': 'N/A'}

        #  rel chng
        # local_map_unique_id_to_avg_abs_changes_last_n_minutes[unique_id] = {'Avg of Abs Changes in Prices Last N Minutes': 'N/A'}

        # Get all legs
        buy_legs = combo_obj.buy_legs
        sell_legs = combo_obj.sell_legs
        all_legs = buy_legs + sell_legs

        # list of request_id
        req_id_list = []

        # Merge Data
        for leg in all_legs:

            action = leg.action
            con_id = leg.con_id
            req_id = map_conid_action_to_req_id[con_id][action]
            req_id_list.append(req_id)

        # Process Data,
        all_data_frames = [
            variables.map_req_id_to_historical_data_dataframe[req_id]
            for req_id in req_id_list
        ]

        # Save DF to CSV File
        if variables.flag_store_cas_tab_csv_files and last_n_minutes_lookback == None:

            for i, df_intraday_legwise in enumerate(all_data_frames):

                # prepare file path
                file_path = rf"{variables.cas_tab_csv_file_path}\Support Resistance And Relative Fields\LegWise"
                file_path += rf"\Unique_id_{unique_id}"

                if not os.path.exists(file_path):
                    os.makedirs(file_path)

                # Save dataframe in csv file
                df_intraday_legwise.to_csv(
                    rf"{file_path}\Leg_{i+1}_support_resistance_and_relative_fields.csv",
                    index=False,
                )
        # Save DF to CSV File
        elif variables.flag_store_cas_tab_csv_files and last_n_minutes_lookback != None:

            for i, df_intraday_legwise in enumerate(all_data_frames):

                file_path = rf"{variables.cas_tab_csv_file_path}\Last N Minutes Fields\LegWise Prices"
                file_path += rf"\Unique_id_{unique_id}"

                if not os.path.exists(file_path):
                    os.makedirs(file_path)

                df_intraday_legwise.to_csv(
                    rf"{file_path}\Leg_{i+1}_Relative_Columns_last_n_minutes.csv",
                    index=False,
                )

        # Data not found for any leg
        is_data_frame_empty = False

        # If data is not present
        for i, historical_dataframe in enumerate(all_data_frames):
            if (
                historical_dataframe is None
                or len(historical_dataframe.index) == 0
                or historical_dataframe.empty
            ):
                is_data_frame_empty = True
                # Print to console
                if variables.flag_debug_mode:
                    print(f"Empty Data Frame : Unqiue ID {unique_id}")
                break

        # Check if data frame is empty
        if is_data_frame_empty:

            # Check if last n minutes inout are none
            if last_n_minutes_lookback == None:

                # Define default values
                local_map_unique_id_to_support_resistance_and_relative_fields[
                    unique_id
                ] = {
                    "Resistance": "N/A",
                    "Support": "N/A",
                    "Resistance Count": "N/A",
                    "Support Count": "N/A",
                    "Relative ATR": "N/A",
                    "Avg of Abs Changes in Prices": "N/A",
                    "Relative ATR Derivative": "N/A",
                    "Relative ATR on Positive Candles": "N/A",
                    "Relative ATR on Negative Candles": "N/A",
                    "Price Support Ratio": "N/A",
                    "Price Resistance Ratio": "N/A",
                    "Relative ATR Lower": "N/A",
                    "Relative ATR Higher": "N/A",
                }

                prices_df_dict[unique_id] = {
                    "Latest Day": "N/A",
                    "Historic Data Except Current Day": "N/A",
                }

            elif last_n_minutes_lookback != None:

                # Define default values
                local_map_unique_id_to_avg_abs_changes_last_n_minutes[unique_id] = {
                    "Relative Change Last N Minutes": "N/A"
                }
            continue

        # Merging the data frame, inner join on time
        merged_df = merge_dataframe_inner_join_with_combo_price_calculation(
            combo_obj, all_data_frames
        )

        # Save DF to CSV File
        if variables.flag_store_cas_tab_csv_files and last_n_minutes_lookback == None:

            # Saving dataframe to csv
            file_path = rf"{variables.cas_tab_csv_file_path}\Support Resistance And Relative Fields\Merged"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            merged_df.to_csv(
                rf"{file_path}\Unique_Id_{unique_id}_Relative_Columns_all_legs_merged.csv",
                index=False,
            )

        elif variables.flag_store_cas_tab_csv_files and last_n_minutes_lookback != None:

            # Saving dataframe to csv
            file_path = rf"{variables.cas_tab_csv_file_path}\Last N Minutes Fields\Merged Prices"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            merged_df.to_csv(
                rf"{file_path}\Unique_Id_{unique_id}_Relative_Columns_last_n_minutes_all_legs_merged.csv",
                index=False,
            )

        # Create new DataFrame with desired columns
        combination_price_dataframe = merged_df[
            ["Time", "Combination Open", "Combination Close"]
        ].copy()

        # Create new DataFrame with legwise columns
        combination_price_dataframe_with_legwise_columns = merged_df.copy()

        try:

            # Create a new dataframe having the latest day available values, and reset index
            latest_available_date = combination_price_dataframe.iloc[-1]["Time"].date()
            latest_day_dataframe = combination_price_dataframe[
                combination_price_dataframe["Time"].dt.date == latest_available_date
            ].copy()
            historical_data_except_current_day_dataframe = combination_price_dataframe[
                combination_price_dataframe["Time"].dt.date < latest_available_date
            ].copy()
            historical_data_except_current_day_dataframe_legwise_columns = (
                combination_price_dataframe_with_legwise_columns[
                    combination_price_dataframe_with_legwise_columns["Time"].dt.date
                    < latest_available_date
                ].copy()
            )

            # copy dataframes
            latest_day_dataframe_prices = latest_day_dataframe.copy()
            historical_data_except_current_day_dataframe_prices = (
                historical_data_except_current_day_dataframe.copy()
            )

            # Reset the index of dataframes
            latest_day_dataframe = latest_day_dataframe.reset_index(drop=True)
            historical_data_except_current_day_dataframe = (
                historical_data_except_current_day_dataframe.reset_index(drop=True)
            )
            historical_data_except_current_day_dataframe_legwise_columns = historical_data_except_current_day_dataframe_legwise_columns.reset_index(
                drop=True
            )

            # Check if last n minutes input are not none
            if last_n_minutes_lookback != None:

                # Create a new dataframe having the previous day available values, and reset index
                previous_available_date = (
                    historical_data_except_current_day_dataframe.iloc[-1]["Time"].date()
                )
                previous_day_dataframe = (
                    combination_price_dataframe_with_legwise_columns[
                        combination_price_dataframe_with_legwise_columns["Time"].dt.date
                        == previous_available_date
                    ].copy()
                )
                historical_data_except_current_and_previous_day_dataframe = (
                    historical_data_except_current_day_dataframe[
                        historical_data_except_current_day_dataframe["Time"].dt.date
                        < previous_available_date
                    ].copy()
                )

                # create dataframe without current and previous day
                historical_data_except_current_and_previous_day_dataframe_legwise_columns = historical_data_except_current_day_dataframe_legwise_columns[
                    historical_data_except_current_day_dataframe_legwise_columns[
                        "Time"
                    ].dt.date
                    < previous_available_date
                ].copy()

                # Reset the index of dataframes
                previous_day_dataframe = previous_day_dataframe.reset_index(drop=True)
                historical_data_except_current_and_previous_day_dataframe = historical_data_except_current_and_previous_day_dataframe.reset_index(
                    drop=True
                )
                historical_data_except_current_and_previous_day_dataframe_legwise_columns = historical_data_except_current_and_previous_day_dataframe_legwise_columns.reset_index(
                    drop=True
                )

                # Get most recent price in previous day
                recent_price_in_previous_day = previous_day_dataframe.loc[
                    previous_day_dataframe.index[-1], "Combination Close"
                ]

                # Get n minute old price of previous day
                past_n_minute_price_in_previous_day = previous_day_dataframe.loc[
                    previous_day_dataframe.index[-2], "Combination Close"
                ]

                # Start Time and End Time for the Relative ATR
                start_time_of_time_slot = previous_day_dataframe.loc[
                    previous_day_dataframe.index[-2], "Time"
                ]
                end_time_of_time_slot = previous_day_dataframe.loc[
                    previous_day_dataframe.index[-1], "Time"
                ]

                # Get the last index of the DataFrame
                last_index = previous_day_dataframe.index[-1]

                previous_day_dataframe = previous_day_dataframe.iloc[
                    -2 : last_index + 1
                ]

                try:
                    # Calculating Average abs change in price for the same time-period averaged over the look back
                    avg_of_abs_changes_in_prices_for_lookback = calculate_avg_of_abs_change_in_price_for_the_same_time_period(
                        unique_id,
                        historical_data_except_current_and_previous_day_dataframe_legwise_columns,
                        start_time_of_time_slot,
                        end_time_of_time_slot,
                        flag_last_n_minute_field=True,
                        local_unique_id_to_combo_obj=local_unique_id_to_combo_obj,
                    )

                    # Update From Open if the flag_weighted_change_in_price is False
                    if not variables.flag_weighted_change_in_price:

                        # Change from open percent
                        rel_chg_last_n_minutes = math.log(
                            abs(recent_price_in_previous_day) + 1
                        ) * math.copysign(1, recent_price_in_previous_day) - math.log(
                            abs(past_n_minute_price_in_previous_day) + 1
                        ) * math.copysign(
                            1, past_n_minute_price_in_previous_day
                        )

                    # Update From Open if the flag_weighted_change_in_price is True
                    if variables.flag_weighted_change_in_price:

                        # Get day open prices for each leg
                        previous_day_last_n_minute_price_for_legs_list = (
                            get_values_for_each_leg(previous_day_dataframe, combo_obj)
                        )

                        # Get most recent prices for legs for previous day
                        previous_day_recent_price_for_legs_list = (
                            get_values_for_each_leg(
                                previous_day_dataframe,
                                combo_obj,
                                combo_price_type_highest_or_lowest_or_current="Current",
                            )
                        )

                        # Calcualte change from prie for last n minutes
                        change_from_past_n_minutes_percent = calc_weighted_change_legs_based(
                            local_unique_id_to_combo_obj[unique_id],
                            previous_day_last_n_minute_price_for_legs_list,
                            most_recent_value_for_day_in_lookback=previous_day_recent_price_for_legs_list,
                        )

                        # Calculate relative change for last n minute in lookback period
                        rel_chg_last_n_minutes = (
                            change_from_past_n_minutes_percent
                            / avg_of_abs_changes_in_prices_for_lookback
                        )

                    # Put values in dictionary
                    local_map_unique_id_to_avg_abs_changes_last_n_minutes[unique_id] = {
                        "Relative Change Last N Minutes": rel_chg_last_n_minutes
                    }

                except Exception as e:

                    # Set to N/A
                    avg_of_abs_changes_in_prices_for_lookback = "N/A"

                    # Print to console
                    if variables.flag_debug_mode:

                        print(
                            f"Exception in calculation of Average abs change in price, Exp: {e}"
                        )

            else:
                # Start Time and End Time for the Relative ATR
                start_time_of_time_slot = latest_day_dataframe.loc[0, "Time"]
                end_time_of_time_slot = latest_day_dataframe.loc[
                    latest_day_dataframe.index[-1], "Time"
                ]

                # Subtract 15 minutes using Timedelta
                end_time_of_time_slot_derivative = end_time_of_time_slot - pd.Timedelta(
                    minutes=variables.relative_atr_derivation_lookback_mins
                )

                # Calculate relative volume
                relative_atr_n_mins_back = atr_div_by_atr_avg(
                    unique_id,
                    latest_day_dataframe.copy(),
                    historical_data_except_current_day_dataframe.copy(),
                    start_time_of_time_slot,
                    end_time_of_time_slot_derivative,
                )

                try:

                    # get copy og dataframe
                    latest_day_dataframe_copy = latest_day_dataframe.copy()

                    # Create a new column 'Previous Close' with the previous row's value from column 'Combination Close'
                    latest_day_dataframe_copy[
                        "Previous Close"
                    ] = latest_day_dataframe_copy["Combination Close"].shift(1)

                    historical_data_except_current_day_dataframe_copy = (
                        historical_data_except_current_day_dataframe.copy()
                    )

                    # Create a new column 'Previous Close' with the previous row's value from column 'Combination Close'
                    historical_data_except_current_day_dataframe_copy[
                        "Previous Close"
                    ] = historical_data_except_current_day_dataframe_copy[
                        "Combination Close"
                    ].shift(
                        1
                    )

                    # Get filterd latest day dataframe
                    latest_day_positive_candles_df = latest_day_dataframe_copy[
                        latest_day_dataframe_copy["Combination Close"]
                        > latest_day_dataframe_copy["Combination Open"]
                    ].copy()
                    latest_day_negative_candles_df = latest_day_dataframe_copy[
                        latest_day_dataframe_copy["Combination Close"]
                        < latest_day_dataframe_copy["Combination Open"]
                    ].copy()

                    # Get filtered historical dataframe
                    historical_data_except_current_day_dataframe_positive_candles_df = (
                        historical_data_except_current_day_dataframe_copy[
                            historical_data_except_current_day_dataframe_copy[
                                "Combination Close"
                            ]
                            > historical_data_except_current_day_dataframe_copy[
                                "Combination Open"
                            ]
                        ].copy()
                    )
                    historical_data_except_current_day_dataframe_negative_candles_df = (
                        historical_data_except_current_day_dataframe_copy[
                            historical_data_except_current_day_dataframe_copy[
                                "Combination Close"
                            ]
                            < historical_data_except_current_day_dataframe_copy[
                                "Combination Open"
                            ]
                        ].copy()
                    )

                    # Save DF to CSV File
                    if variables.flag_store_cas_tab_csv_files:

                        # Saving dataframe to csv
                        file_path = rf"{variables.cas_tab_csv_file_path}\Support Resistance And Relative Fields\Current Day Positive_Negative Candles"

                        if not os.path.exists(file_path):
                            os.makedirs(file_path)

                        latest_day_positive_candles_df.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_prices__positive_candles.csv",
                            index=False,
                        )

                        latest_day_negative_candles_df.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_prices_negative_candles.csv",
                            index=False,
                        )

                        # Saving dataframe to csv
                        file_path = rf"{variables.cas_tab_csv_file_path}\Support Resistance And Relative Fields\Historical Days Except Current Day Positive Negative Candles"

                        if not os.path.exists(file_path):
                            os.makedirs(file_path)


                        historical_data_except_current_day_dataframe_positive_candles_df.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_prices__positive_candles.csv",
                            index=False,
                        )

                        historical_data_except_current_day_dataframe_negative_candles_df.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_prices_negative_candles.csv",
                            index=False,
                        )

                    # Rel ATR - ATR for a particular period of time in the day / Avg ATR for the same time period averaged over the look back
                    relative_atr_positive_candles = atr_div_by_atr_avg(
                        unique_id,
                        latest_day_positive_candles_df.copy(),
                        historical_data_except_current_day_dataframe_positive_candles_df.copy(),
                        start_time_of_time_slot,
                        end_time_of_time_slot,
                        flag_positive_negative_candle=True,
                    )

                    # Rel ATR - ATR for a particular period of time in the day / Avg ATR for the same time period averaged over the look back
                    relative_atr_negative_candles = atr_div_by_atr_avg(
                        unique_id,
                        latest_day_negative_candles_df.copy(),
                        historical_data_except_current_day_dataframe_negative_candles_df.copy(),
                        start_time_of_time_slot,
                        end_time_of_time_slot,
                        flag_positive_negative_candle=True,
                    )

                except Exception as e:

                    # Set to N/A
                    relative_atr_positive_candles = "N/A"
                    relative_atr_negative_candles = "N/A"

                    # Print to console
                    if variables.flag_debug_mode:

                        print(
                            f"Exception in getting positive and negative candles dataframe for ATR, Exp: {e}"
                        )

                # Code to calculate rleative ATR for lowest range
                try:

                    latest_day_dataframe_copy = latest_day_dataframe.copy()

                    # Create a new column 'Previous Close' with the previous row's value from column 'Combination Close'
                    latest_day_dataframe_copy[
                        "Previous Close"
                    ] = latest_day_dataframe_copy["Combination Close"].shift(1)

                    historical_data_except_current_day_dataframe_copy = (
                        historical_data_except_current_day_dataframe.copy()
                    )

                    # Create a new column 'Previous Close' with the previous row's value from column 'Combination Close'
                    historical_data_except_current_day_dataframe_copy[
                        "Previous Close"
                    ] = historical_data_except_current_day_dataframe_copy[
                        "Combination Close"
                    ].shift(
                        1
                    )

                    # Get the minimum and maximum values of column 'Combination Close'
                    min_value = combination_price_dataframe["Combination Close"].min()
                    max_value = combination_price_dataframe["Combination Close"].max()

                    # check if number of buckets is 0
                    if variables.relative_atr_in_range_number_of_buckets == 0:

                        raise Exception("Number of buckets is 0")

                    # get size of bucket
                    size_of_bucket = (
                        max_value - min_value
                    ) / variables.relative_atr_in_range_number_of_buckets

                    # get lower range
                    lower_range = [min_value, min_value + size_of_bucket]

                    # get higher range
                    higher_range = [max_value - size_of_bucket, max_value]

                    # check if flag is close in rnage
                    if variables.flag_relative_atr_in_range == "Close In Range":

                        # Get filterd latest day dataframe
                        latest_day_lower_range_df = latest_day_dataframe_copy[
                            (
                                latest_day_dataframe_copy["Combination Close"]
                                >= lower_range[0]
                            )
                            & (
                                latest_day_dataframe_copy["Combination Close"]
                                <= lower_range[1]
                            )
                        ].copy()
                        latest_day_higher_range_df = latest_day_dataframe_copy[
                            (
                                latest_day_dataframe_copy["Combination Close"]
                                >= higher_range[0]
                            )
                            & (
                                latest_day_dataframe_copy["Combination Close"]
                                <= higher_range[1]
                            )
                        ].copy()

                        # Get filtered historical dataframe
                        historical_data_except_current_day_dataframe_lower_range_df = (
                            historical_data_except_current_day_dataframe_copy[
                                (
                                    historical_data_except_current_day_dataframe_copy[
                                        "Combination Close"
                                    ]
                                    >= lower_range[0]
                                )
                                & (
                                    historical_data_except_current_day_dataframe_copy[
                                        "Combination Close"
                                    ]
                                    <= lower_range[1]
                                )
                            ].copy()
                        )
                        historical_data_except_current_day_dataframe_higher_range_df = (
                            historical_data_except_current_day_dataframe_copy[
                                (
                                    historical_data_except_current_day_dataframe_copy[
                                        "Combination Close"
                                    ]
                                    >= higher_range[0]
                                )
                                & (
                                    historical_data_except_current_day_dataframe_copy[
                                        "Combination Close"
                                    ]
                                    <= higher_range[1]
                                )
                            ].copy()
                        )

                    # check if flag is open in rnage
                    elif variables.flag_relative_atr_in_range == "Open In Range":

                        # Get filterd latest day dataframe
                        latest_day_lower_range_df = latest_day_dataframe_copy[
                            (
                                latest_day_dataframe_copy["Combination Open"]
                                >= lower_range[0]
                            )
                            & (
                                latest_day_dataframe_copy["Combination Open"]
                                <= lower_range[1]
                            )
                        ].copy()
                        latest_day_higher_range_df = latest_day_dataframe_copy[
                            (
                                latest_day_dataframe_copy["Combination Open"]
                                >= higher_range[0]
                            )
                            & (
                                latest_day_dataframe_copy["Combination Open"]
                                <= higher_range[1]
                            )
                        ].copy()

                        # Get filtered historical dataframe
                        historical_data_except_current_day_dataframe_lower_range_df = (
                            historical_data_except_current_day_dataframe_copy[
                                (
                                    historical_data_except_current_day_dataframe_copy[
                                        "Combination Open"
                                    ]
                                    >= lower_range[0]
                                )
                                & (
                                    historical_data_except_current_day_dataframe_copy[
                                        "Combination Open"
                                    ]
                                    <= lower_range[1]
                                )
                            ].copy()
                        )
                        historical_data_except_current_day_dataframe_higher_range_df = (
                            historical_data_except_current_day_dataframe_copy[
                                (
                                    historical_data_except_current_day_dataframe_copy[
                                        "Combination Open"
                                    ]
                                    >= higher_range[0]
                                )
                                & (
                                    historical_data_except_current_day_dataframe_copy[
                                        "Combination Open"
                                    ]
                                    <= higher_range[1]
                                )
                            ].copy()
                        )

                    else:

                        # Get filterd latest day dataframe
                        latest_day_lower_range_df = latest_day_dataframe_copy[
                            (
                                latest_day_dataframe_copy["Combination Open"].between(
                                    lower_range[0], lower_range[1]
                                )
                                | latest_day_dataframe_copy[
                                    "Combination Close"
                                ].between(lower_range[0], lower_range[1])
                            )
                        ].copy()
                        latest_day_higher_range_df = latest_day_dataframe_copy[
                            (
                                latest_day_dataframe_copy["Combination Open"].between(
                                    higher_range[0], higher_range[1]
                                )
                                | latest_day_dataframe_copy[
                                    "Combination Close"
                                ].between(higher_range[0], higher_range[1])
                            )
                        ].copy()

                        # Get filtered historical dataframe
                        historical_data_except_current_day_dataframe_lower_range_df = (
                            historical_data_except_current_day_dataframe_copy[
                                (
                                    historical_data_except_current_day_dataframe_copy[
                                        "Combination Open"
                                    ].between(lower_range[0], lower_range[1])
                                    | historical_data_except_current_day_dataframe_copy[
                                        "Combination Close"
                                    ].between(lower_range[0], lower_range[1])
                                )
                            ].copy()
                        )
                        historical_data_except_current_day_dataframe_higher_range_df = (
                            historical_data_except_current_day_dataframe_copy[
                                (
                                    historical_data_except_current_day_dataframe_copy[
                                        "Combination Open"
                                    ].between(higher_range[0], higher_range[1])
                                    | historical_data_except_current_day_dataframe_copy[
                                        "Combination Close"
                                    ].between(higher_range[0], higher_range[1])
                                )
                            ].copy()
                        )

                    # Save DF to CSV File
                    if variables.flag_store_cas_tab_csv_files:

                        # Saving dataframe to csv
                        file_path = rf"{variables.cas_tab_csv_file_path}\Relative Fields in Range\Current Day Lower Higher Range Prices"

                        if not os.path.exists(file_path):
                            os.makedirs(file_path)

                        latest_day_lower_range_df.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_prices_lower_range.csv",
                            index=False,
                        )

                        latest_day_higher_range_df.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_prices_higher_range.csv",
                            index=False,
                        )

                        # Saving dataframe to csv
                        file_path = rf"{variables.cas_tab_csv_file_path}\Relative Fields in Range\Historical Days Except Current Day Lower Higher Range Prices"

                        if not os.path.exists(file_path):
                            os.makedirs(file_path)

                        historical_data_except_current_day_dataframe_lower_range_df.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_prices_lower_range.csv",
                            index=False,
                        )

                        historical_data_except_current_day_dataframe_higher_range_df.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_prices_higher_range.csv",
                            index=False,
                        )

                    # print(latest_day_lower_range_df.to_string())
                    # Rel ATR - ATR for a particular period of time in the day / Avg ATR for the same time period averaged over the look back
                    relative_atr_lower_range = atr_div_by_atr_avg(
                        unique_id,
                        latest_day_lower_range_df.copy(),
                        historical_data_except_current_day_dataframe_lower_range_df.copy(),
                        start_time_of_time_slot,
                        end_time_of_time_slot,
                        flag_positive_negative_candle=True,
                    )

                    # Rel ATR - ATR for a particular period of time in the day / Avg ATR for the same time period averaged over the look back
                    relative_atr_higher_range = atr_div_by_atr_avg(
                        unique_id,
                        latest_day_higher_range_df.copy(),
                        historical_data_except_current_day_dataframe_higher_range_df.copy(),
                        start_time_of_time_slot,
                        end_time_of_time_slot,
                        flag_positive_negative_candle=True,
                    )

                    # print([relative_atr_lower_range, relative_atr_higher_range])

                except Exception as e:

                    relative_atr_lower_range = "N/A"
                    relative_atr_higher_range = "N/A"

                    # Print to console
                    if variables.flag_debug_mode:

                        print(
                            f"Exception in getting positive and negative candles dataframe for ATR, Exp: {e}"
                        )

                try:
                    # Check flag indicating which candles to use either since start of day or current candle
                    if (
                        not variables.flag_since_start_of_day_candles_for_relative_fields
                    ):

                        # Rel ATR - ATR for a particular period of time in the day / Avg ATR for the same time period averaged over the look back
                        relative_atr_current = atr_div_by_atr_avg(
                            unique_id,
                            latest_day_dataframe.copy(),
                            historical_data_except_current_day_dataframe.copy(),
                            start_time_of_time_slot,
                            end_time_of_time_slot,
                        )

                        # set start time of rel atr
                        start_time_of_time_slot = latest_day_dataframe.loc[
                            latest_day_dataframe.index[-2], "Time"
                        ]

                        # Editing dataframe to have current candle only
                        latest_day_dataframe = latest_day_dataframe.tail(2)

                        # Reset index
                        latest_day_dataframe = latest_day_dataframe.reset_index(
                            drop=True
                        )
                except Exception as e:

                    # Set to N/A
                    start_time_of_time_slot = "N/A"

                    # Print to console
                    if variables.flag_debug_mode:

                        print(
                            f"Exception inside getting time slots for relative ATR, Exp: {e}"
                        )

                try:

                    # Rel ATR - ATR for a particular period of time in the day / Avg ATR for the same time period averaged over the look back
                    relative_atr = atr_div_by_atr_avg(
                        unique_id,
                        latest_day_dataframe.copy(),
                        historical_data_except_current_day_dataframe.copy(),
                        start_time_of_time_slot,
                        end_time_of_time_slot,
                    )

                    # Calculating Average abs change in price for the same time-period averaged over the look back
                    avg_of_abs_changes_in_prices_for_lookback = calculate_avg_of_abs_change_in_price_for_the_same_time_period(
                        unique_id,
                        historical_data_except_current_day_dataframe_legwise_columns,
                        start_time_of_time_slot,
                        end_time_of_time_slot,
                        local_unique_id_to_combo_obj=local_unique_id_to_combo_obj,
                    )

                    # Check flag indicating which candles to use either since start of day or current candle
                    if (
                        not variables.flag_since_start_of_day_candles_for_relative_fields
                    ):

                        # calcualte rlative ATR derivative
                        relative_atr_derivative = (
                            relative_atr_current / relative_atr_n_mins_back
                        )

                    else:

                        # calcualte rlative ATR derivative
                        relative_atr_derivative = (
                            relative_atr / relative_atr_n_mins_back
                        )

                except Exception as e:

                    # Set to N/A
                    relative_atr = "N/A"

                    avg_of_abs_changes_in_prices_for_lookback = "N/A"

                    relative_atr_derivative = "N/A"

                    # Print to console
                    if variables.flag_debug_mode:

                        print(f"Exception in calculation of relative ATR, Exp: {e}")

                # Support resisatance, counts
                list_of_candles = [
                    combination_price_dataframe["Combination Open"].tolist(),
                    combination_price_dataframe["Combination Close"].tolist(),
                ]
                (
                    significant_level,
                    significant_level_count_values,
                ) = calc_signficant_levels(
                    list_of_candles,
                )

                # Check if combo is actual combo not leg
                if unique_id > 0:

                    # Calculate significant levels
                    (
                        significant_level_in_range,
                        significant_level_count_values_in_range,
                    ) = calc_signficant_levels(
                        list_of_candles, flag_in_range=True, unique_id=unique_id
                    )

                else:

                    # Calculate significant levels
                    (
                        significant_level_in_range,
                        significant_level_count_values_in_range,
                    ) = calc_signficant_levels(
                        list_of_candles, flag_in_range=True, unique_id=unique_id, combo_obj=combo_obj
                    )

                # Defining resistance and support variables
                resistance, support = "N/A", "N/A"

                # Defining resistance count and support count variables
                resistane_count, support_count = "N/A", "N/A"

                # Defining resistance and support variables
                resistance_in_range, support_in_range = "N/A", "N/A"

                # Defining resistance count and support count variables
                resistane_count_in_range, support_count_in_range = "N/A", "N/A"

                try:

                    # Init
                    resistance, support = "N/A", "N/A"
                    resistance_count, support_count = "N/A", "N/A"

                    # GEt cuurent price
                    if unique_id in local_unique_id_to_prices_dict:

                        current_buy_price, current_sell_price = (
                            local_unique_id_to_prices_dict[unique_id]["BUY"],
                            local_unique_id_to_prices_dict[unique_id]["SELL"],
                        )



                        # Calculating the Resistance, Support
                        (
                            resistance,
                            support,
                        ) = get_support_and_resitance_from_significant_levels(
                            significant_level, current_buy_price, current_sell_price
                        )

                        # Calculating the Resistance count, Support count
                        if resistance not in ["N/A", None, "None"]:
                            resistance_count = significant_level_count_values[
                                resistance
                            ]
                        else:
                            resistance_count = "N/A"

                        if support not in ["N/A", None, "None"]:
                            support_count = significant_level_count_values[support]
                        else:
                            support_count = "N/A"

                    else:

                        # check if it is leg value calcualtions
                        if len(all_legs) > 1:
                            current_buy_price, current_sell_price = 'N/A', 'N/A'

                        # Get current price for legs
                        for leg_obj in all_legs:
                            req_id = variables.con_id_to_req_id_dict[leg_obj.con_id]
                            bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]
                            current_buy_price, current_sell_price = ask, bid



                        # Calculating the Resistance, Support
                        (
                            resistance,
                            support,
                        ) = get_support_and_resitance_from_significant_levels(
                            significant_level, current_buy_price, current_sell_price
                        )

                        # Calculating the Resistance count, Support count
                        if resistance not in ["N/A", None, "None"]:
                            resistance_count = significant_level_count_values[
                                resistance
                            ]
                        else:
                            resistance_count = "N/A"

                        if support not in ["N/A", None, "None"]:
                            support_count = significant_level_count_values[support]
                        else:
                            support_count = "N/A"



                except Exception as e:

                    # Set to N/S
                    resistance, support = "N/A", "N/A"
                    resistance_count, support_count = "N/A", "N/A"

                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Exception Occured For calculating intraday resistance and support, error is {e}"
                        )

                try:

                    # Init
                    resistance_in_range, support_in_range = "N/A", "N/A"

                    # Get curerent price of combo
                    if unique_id in local_unique_id_to_prices_dict:

                        current_buy_price, current_sell_price = (
                            local_unique_id_to_prices_dict[unique_id]["BUY"],
                            local_unique_id_to_prices_dict[unique_id]["SELL"],
                        )

                        # Calculating the Resistance, Support
                        (
                            resistance_in_range,
                            support_in_range,
                        ) = get_support_and_resitance_from_significant_levels(
                            significant_level_in_range,
                            current_buy_price,
                            current_sell_price,
                        )

                        # get average combo price
                        avg_price_combo = (
                            variables.unique_id_to_prices_dict[unique_id]["BUY"]
                            + variables.unique_id_to_prices_dict[unique_id]["SELL"]
                        ) / 2

                        # Check if values are valid
                        if avg_price_combo not in [
                            "N/A",
                            None,
                            "None",
                        ] and support_in_range not in ["N/A", None, "None"]:

                            support_in_range = support_in_range - avg_price_combo

                        else:

                            support_in_range = "N/A"

                        # Check if values are valid
                        if avg_price_combo not in [
                            "N/A",
                            None,
                            "None",
                        ] and resistance_in_range not in ["N/A", None, "None"]:

                            resistance_in_range = resistance_in_range - avg_price_combo

                        else:

                            resistance_in_range = "N/A"

                        # Calculating the Resistance count, Support count
                        """if resistance_in_range not in ["N/A", None, "None"]:
                            resistance_count_in_range = significant_level_count_values_in_range[resistance_in_range]
                        else:
                            resistance_count_in_range = 'N/A'

                        if support_in_range not in ["N/A", None, "None"]:
                            support_count_in_range = significant_level_count_values_in_range[support_in_range]
                        else:
                            support_count_in_range = 'N/A""" ""

                    else:

                        # checking of its leg cmbo
                        if len(all_legs) > 1:
                            current_buy_price, current_sell_price = 'N/A', 'N/A'

                        # Get current price for leg
                        for leg_obj in all_legs:
                            req_id = variables.con_id_to_req_id_dict[leg_obj.con_id]
                            bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]
                            current_buy_price, current_sell_price = ask, bid

                        # Calculating the Resistance, Support
                        (
                            resistance_in_range,
                            support_in_range,
                        ) = get_support_and_resitance_from_significant_levels(
                            significant_level_in_range,
                            current_buy_price,
                            current_sell_price,
                        )

                        # get average combo price
                        avg_price_combo = (
                                                  current_buy_price
                                                  + current_sell_price
                                          ) / 2

                        # Check if values are valid
                        if avg_price_combo not in [
                            "N/A",
                            None,
                            "None",
                        ] and support_in_range not in ["N/A", None, "None"]:

                            support_in_range = support_in_range - avg_price_combo

                        else:

                            support_in_range = "N/A"

                        # Check if values are valid
                        if avg_price_combo not in [
                            "N/A",
                            None,
                            "None",
                        ] and resistance_in_range not in ["N/A", None, "None"]:

                            resistance_in_range = resistance_in_range - avg_price_combo

                        else:

                            resistance_in_range = "N/A"


                        # resistance_count_in_range, support_count_in_range = 'N/A', 'N/A'
                except Exception as e:

                    # Set to N/A
                    resistance_in_range, support_in_range = "N/A", "N/A"
                    # resistance_count_in_range, support_count_in_range = 'N/A', 'N/A'

                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Exception Occured For calculating intraday resistance and support in range, error is {e}"
                        )


                # Assign calcualted values
                local_map_unique_id_to_support_resistance_and_relative_fields[
                    unique_id
                ] = {
                    "Resistance": resistance,
                    "Support": support,
                    "Resistance Count": resistance_count,
                    "Support Count": support_count,
                    "Relative ATR": relative_atr,
                    "Avg of Abs Changes in Prices": avg_of_abs_changes_in_prices_for_lookback,
                    "Relative ATR Derivative": relative_atr_derivative,
                    "Relative ATR on Positive Candles": relative_atr_positive_candles,
                    "Relative ATR on Negative Candles": relative_atr_negative_candles,
                    "Price Support Ratio": support_in_range,
                    "Price Resistance Ratio": resistance_in_range,
                    "Relative ATR Lower": relative_atr_lower_range,
                    "Relative ATR Higher": relative_atr_higher_range,
                }
                '''if unique_id < 0:

                    print(local_map_unique_id_to_support_resistance_and_relative_fields[
                    unique_id
                    ])'''

                # Assign df in dict
                prices_df_dict[unique_id] = {
                    "Latest Day": latest_day_dataframe_prices,
                    "Historic Data Except Current Day": historical_data_except_current_day_dataframe_prices,
                    "Latest Day Lower Range": latest_day_lower_range_df,
                    "Latest Day Higher Range": latest_day_higher_range_df,
                    "Historic Data Except Current Day Lower Range": historical_data_except_current_day_dataframe_lower_range_df,
                    "Historic Data Except Current Day Higher Range": historical_data_except_current_day_dataframe_higher_range_df,
                }

        except Exception as e:

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Unique ID : {unique_id}, Error inside of calculating Support Resistance and Relative fields Related columns : {e}"
                )

    # Check if last n minutes inout are none
    if last_n_minutes_lookback == None:

        return (
            local_map_unique_id_to_support_resistance_and_relative_fields,
            prices_df_dict,
        )

    # If input for last n minutes are available
    elif last_n_minutes_lookback != None:

        return local_map_unique_id_to_avg_abs_changes_last_n_minutes

# Method to calcuulate bid ask related indicators
def calculate_bid_ask_indicators(
    local_unique_id_to_combo_obj, map_conid_action_to_req_id, prices_df_dict
):

    # Init dict
    local_map_unique_id_tobid_ask_relative_fields = {}

    local_unique_id_to_prices_dict = copy.deepcopy(variables.unique_id_to_prices_dict)

    for unique_id, combo_obj in local_unique_id_to_combo_obj.items():

        # Define default values
        local_map_unique_id_tobid_ask_relative_fields[unique_id] = {
            "Average Bid Ask": "N/A",
        }

        # Get legs of combo
        buy_legs = combo_obj.buy_legs
        sell_legs = combo_obj.sell_legs
        all_legs = buy_legs + sell_legs

        # list of request_id
        req_id_list_ask = []

        # list of request_id
        req_id_list_bid = []

        # Merge Data
        for leg in all_legs:
            action = leg.action
            con_id = leg.con_id
            req_id = map_conid_action_to_req_id[con_id]["BUY"]
            req_id_list_ask.append(req_id)
            req_id = map_conid_action_to_req_id[con_id]["SELL"]
            req_id_list_bid.append(req_id)

        # Process Data,
        all_data_frames = [
            variables.map_req_id_to_historical_data_dataframe[req_id]
            for req_id in req_id_list_ask
        ] + [
            variables.map_req_id_to_historical_data_dataframe[req_id]
            for req_id in req_id_list_bid
        ]

        # ask price dataframes
        ask_data_frames = [
            variables.map_req_id_to_historical_data_dataframe[req_id]
            for req_id in req_id_list_ask
        ]

        # bid prices dataframes
        bid_data_frames = [
            variables.map_req_id_to_historical_data_dataframe[req_id]
            for req_id in req_id_list_bid
        ]

        # Data not found for any leg
        is_data_frame_empty = False

        # If data is not present
        for i, historical_dataframe in enumerate(all_data_frames):
            if (
                historical_dataframe is None
                or len(historical_dataframe.index) == 0
                or historical_dataframe.empty
            ):
                is_data_frame_empty = True
                # Print to console
                if variables.flag_debug_mode:
                    print(f"Empty Data Frame : Unqiue ID {unique_id}")
                break

        # Check if data frame is empty
        if is_data_frame_empty:

            # Define default values
            local_map_unique_id_tobid_ask_relative_fields[unique_id] = {
                "Average Bid Ask": "N/A",
            }

            continue

        # Get merger datarame
        merged_df = merge_dataframe_inner_join_with_bid_ask_calculation(
            combo_obj, ask_data_frames, bid_data_frames
        )

        # Create df with 3 columns
        combination_bid_ask_df = merged_df[
            ["Time", "Combination Ask", "Combination Bid"]
        ].copy()

        # Add new column for bid ask spread
        combination_bid_ask_df["Combination Bid Ask Spread"] = (
            combination_bid_ask_df["Combination Ask"]
            - combination_bid_ask_df["Combination Bid"]
        )

        merged_df["Combination Bid Ask Spread"] = combination_bid_ask_df[
            "Combination Bid Ask Spread"
        ]

        # Save DF to CSV File (HV) Export data-frame to csv file
        if variables.flag_store_cas_tab_csv_files:

            file_path = rf"{variables.cas_tab_csv_file_path}\Bid Ask Related Columns\Average Bid Ask Prices"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            # Saving CSV
            merged_df.to_csv(
                rf"{file_path}\{unique_id}_avg_bid_ask_prices.csv", index=False
            )

        try:

            # Calcualte avg bid ask spread since day start
            avg_bid_ask_spread_latest_day = combination_bid_ask_df[
                "Combination Bid Ask Spread"
            ].mean()

        except Exception as e:

            # set value to N/A
            avg_bid_ask_spread_latest_day = "N/A"

            if variables.flag_debug_mode:

                print(f"Exception calcualting average bid ask spread, Exp: {e}")

        # Assign value in dict
        local_map_unique_id_tobid_ask_relative_fields[unique_id] = {
            "Average Bid Ask": avg_bid_ask_spread_latest_day,
        }

    return local_map_unique_id_tobid_ask_relative_fields

# Method to fetch historical volume
def get_historical_volume_for_all_combinations(
    cas_coinds_for_fetching_historical_data, duration_size, bar_size
):

    # Map of [conid][action] = req_id
    map_conid_to_req_id = {}

    # List of all request ids
    req_id_list = []

    for conid, sub_info_dict in cas_coinds_for_fetching_historical_data.items():
        contract = variables.map_con_id_to_contract[conid]

        # Create dict with conid as key
        if conid not in map_conid_to_req_id:
            map_conid_to_req_id[conid] = None
        else:
            continue

        # Getting req_id
        reqId = variables.cas_app.nextorderId
        variables.cas_app.nextorderId += 1

        # Historical Data to ReqId
        map_conid_to_req_id[conid] = reqId

        # append reqid it to the list
        req_id_list.append(reqId)

        # What to show
        what_to_show = "TRADES"

        # Get the historical data
        request_historical_price_data_for_contract(
            contract, bar_size, duration_size, what_to_show, req_id=reqId, cas_app=True
        )

    counter = 0

    # Waiting for hostorical data
    while variables.cas_wait_time_for_historical_data > (
        counter * variables.sleep_time_waiting_for_tws_response
    ):

        """dict_mkt_end = variables.req_mkt_data_end
        dicterr_msg = variables.req_error

        merged_dict = {}

        for key in set(dict_mkt_end.keys()) | set(dicterr_msg.keys()):
            if key in dict_mkt_end and key in dicterr_msg:
                merged_dict[key] = dict_mkt_end[key] or dicterr_msg[key]
            elif key in dict_mkt_end:
                merged_dict[key] = dict_mkt_end[key]
            else:
                merged_dict[key] = dicterr_msg[key]

        # If reqHistorical Data ended for all the reqId
        if all([merged_dict[req_id] for req_id in req_id_list]):
            break"""

        if all(
            [
                variables.req_mkt_data_end[req_id] or variables.req_error[req_id]
                for req_id in req_id_list
            ]
        ):
            break

        # Sleep for sleep_time_waiting_for_tws_response
        time.sleep(variables.sleep_time_waiting_for_tws_response)

        # Increase Counter
        counter += 1

    return map_conid_to_req_id

# Method to calcualte net volume
def formula_to_calculate_net_volume_for_historical_data(
    row, volume, all_data_frames, factors
):
    # Init
    effective_volume_for_legs_list = []

    # Iterate all dfs
    for leg_no in range(len(all_data_frames)):

        column_name = f"{volume} {leg_no + 1}"

        # Get combo volume
        effective_volume_for_legs_list.append(float(row[column_name]) / factors[leg_no])

    try:

        # Calculate net volume
        net_volume = sum(effective_volume_for_legs_list) / len(
            effective_volume_for_legs_list
        )
    except Exception as e:

        # Default Val
        net_volume = "N/A"

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Exception while calculating net volume, formula_to_calculate_net_volume_for_historical_data {e}"
            )

    return net_volume

# Merge dataframe for combnation volume calcualtion
def merge_dataframe_inner_join_with_combo_net_volume_calculation(
    combo_obj, all_data_frames
):

    # All legs in combo
    all_legs = combo_obj.buy_legs + combo_obj.sell_legs

    # Removing the open and close column
    for ith_leg in range(len(all_data_frames)):
        all_data_frames[ith_leg] = all_data_frames[ith_leg].drop(
            ["Open", "Close"], axis=1
        )

    # 1st Data Frame
    merged_df = all_data_frames[0]

    # Merging all data frames such that Time is available in all data frames
    for i, df_ith in enumerate(all_data_frames[1:]):
        merged_df = pd.merge(
            merged_df, df_ith, on="Time", how="inner", suffixes=(f"", f" {i+1}")
        )

    # Dropping nan values, if any
    merged_df = merged_df.dropna()

    # Creating Columns for merged dataframe
    merged_df_columns = ["Time"]

    # Open and Close with leg
    for i in range(len(all_data_frames)):
        merged_df_columns.append(f"Volume {i+1}")

    # Setting columns in merged_df
    merged_df.columns = merged_df_columns

    # Multipling Factors to calculate the historical price of combination
    factors = []

    # Calculating Factor ( mulitplier * leg_qty * (+1 if buy else -1) )
    for leg_obj in all_legs:
        sec_type = leg_obj.sec_type
        quantity = int(leg_obj.quantity)

        # For STK Real volume is * 100 more than the volume received from TWS, so to adjust that in net volume calculation for each legs contribution.
        # we are dividing it by the 1/100 here.
        multiplier = (1 / 100) if sec_type == "STK" else 1

        # If buying +ve factor else -ve
        if leg_obj.action == "BUY":
            factors.append(quantity * multiplier)
        else:
            factors.append(quantity * multiplier)

    # Calculating combination volume
    merged_df["Combination Volume"] = merged_df.apply(
        lambda row: formula_to_calculate_net_volume_for_historical_data(
            row, "Volume", all_data_frames, factors
        ),
        axis=1,
    )
    return merged_df


# Calculate average of combinational volume for given dataframe
def calculate_avg_volume_for_dataframe(combinational_volume_dataframe):

    try:

        # Check if df is empty
        if combinational_volume_dataframe.empty:

            return "N/A"

        # Calculate mean of combinational volume column
        average_volume_for_dataframe_value = combinational_volume_dataframe[
            "Combination Volume"
        ].sum()
    except Exception as e:
        print(f"Inside calculate average volume for dataframe , error is {e}")
    return average_volume_for_dataframe_value


# Calculate Volume since start of the day / Average Volume for the same time-period averaged over the look back
def calculate_relative_volume(
    unique_id,
    latest_day_dataframe,
    historical_data_except_current_day_dataframe,
    date_time_start,
    date_time_close,
    flag_last_n_minute_field=False,
):

    # Convert the 'Time' column to datetime type if it's not already
    historical_data_except_current_day_dataframe["Time"] = pd.to_datetime(
        historical_data_except_current_day_dataframe["Time"]
    )

    # Filter the rows where the time is between start and end time
    filtered_historical_data_dataframe = historical_data_except_current_day_dataframe[
        (
            historical_data_except_current_day_dataframe["Time"].dt.time
            >= pd.to_datetime(date_time_start).time()
        )
        & (
            historical_data_except_current_day_dataframe["Time"].dt.time
            <= pd.to_datetime(date_time_close).time()
        )
    ].reset_index(drop=True)

    # Calculate Volume since start of the day
    volume_since_start_of_day = calculate_avg_volume_for_dataframe(latest_day_dataframe)

    # All dates
    all_date_values = historical_data_except_current_day_dataframe[
        "Time"
    ].dt.date.unique()

    # Get All DataFrames for particular date consisting of combo open close for the specified time range
    all_dataframes_filtered_by_date_in_look_back = []

    # Calculate Volume for particular time on each lookback day
    calculated_volume_for_look_back_days = []

    for date_ith in all_date_values:

        # Filtering the dataframe for the 'date_ith'
        date_specific_dataframe_for_volume = filtered_historical_data_dataframe[
            filtered_historical_data_dataframe["Time"].dt.date == date_ith
        ].reset_index(drop=True)

        # Save DF to CSV File (HV) Export data-frame to csv file
        if (variables.flag_store_cas_tab_csv_files) and not flag_last_n_minute_field:

            file_path = (
                rf"{variables.cas_tab_csv_file_path}\Relative Volume\RelativeVolume"
            )

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            # Saving CSV
            date_specific_dataframe_for_volume.to_csv(
                rf"{file_path}\{unique_id}_relv_volume_{date_ith}.csv", index=False
            )

        # Save DF to CSV File (HV) Export data-frame to csv file
        if (variables.flag_store_cas_tab_csv_files) and flag_last_n_minute_field:

            file_path = rf"{variables.cas_tab_csv_file_path}\Last N Minutes Fields\RelativeVolume"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            # Saving CSV
            date_specific_dataframe_for_volume.to_csv(
                rf"{file_path}\{unique_id}_relv_volume_{date_ith}.csv", index=False
            )

        # Calculating the average volume for each day in lookback period
        calculated_volume_for_look_back_days.append(
            calculate_avg_volume_for_dataframe(date_specific_dataframe_for_volume)
        )

        # Filter the list to keep only int or float items
        calculated_volume_for_look_back_days = [
            x
            for x in calculated_volume_for_look_back_days
            if isinstance(x, (int, float))
        ]

    try:
        # Calculate Avg volume for the same time period averaged over the look back
        volume_avg_over_lookback_period = sum(
            calculated_volume_for_look_back_days
        ) / len(calculated_volume_for_look_back_days)

        # check if value is valid for dividation
        if volume_avg_over_lookback_period not in [0, "N/A", None, "None"]:

            # calculate Volume since start of the day / Average Volume for the same time-period averaged over the look back
            relative_volume = round(
                volume_since_start_of_day / volume_avg_over_lookback_period, 2
            )

        else:

            relative_volume = "N/A"
    except Exception as e:

        # Print to console
        if variables.flag_debug_mode:
            print(
                f"Calculating Realtive volume 'calculate_relative_volume' Exception: {e}"
            )

        relative_volume = "N/A"

    return relative_volume

# Calcualte volume related fields
def calculate_volume_related_fields(
    local_unique_id_to_combo_obj,
    map_conid_to_req_id,
    last_n_minutes_lookback=None,
    prices_df_dict=None,
):

    # Check if last n minutes parameter is None
    if last_n_minutes_lookback == None:

        # Dict
        local_map_unique_id_to_relative_volume_field = {}

    # check if last n minutes parameter is available
    else:

        # Dict
        local_map_unique_id_to_last_n_minutes_field = {}

    # Local copy of live price
    local_unique_id_to_prices_dict = copy.deepcopy(variables.unique_id_to_prices_dict)

    for unique_id, combo_obj in local_unique_id_to_combo_obj.items():

        # Check if last n minutes parameter is None
        if last_n_minutes_lookback == None:

            # Dict
            local_map_unique_id_to_relative_volume_field[unique_id] = {
                "Relative Volume": "N/A",
                "Relative Volume Derivative": "N/A",
                "Relative Volume on Positive Candles": "N/A",
                "Relative Volume on Negative Candles": "N/A",
                "Relative Volume on Lower Range": "N/A",
                "Relative Volume on Higher Range": "N/A",
            }

        # check if last n minutes parameter is available
        else:

            # Dict
            local_map_unique_id_to_last_n_minutes_field[unique_id] = {
                "Relative Volume Last N Minutes": "N/A"
            }

        # Get all legs
        buy_legs = combo_obj.buy_legs
        sell_legs = combo_obj.sell_legs
        all_legs = buy_legs + sell_legs

        # list of request_id
        req_id_list = []

        # Getting all the reqId for which the historical data was requested
        for leg in all_legs:

            con_id = leg.con_id
            req_id = map_conid_to_req_id[con_id]
            req_id_list.append(req_id)

        # Getting all the Dataframes for the legs, Process Data,
        all_data_frames = [
            variables.map_req_id_to_historical_data_dataframe[req_id]
            for req_id in req_id_list
        ]

        # Save DF to CSV File
        if variables.flag_store_cas_tab_csv_files and last_n_minutes_lookback == None:

            for i, df_xxx in enumerate(all_data_frames):

                file_path = (
                    rf"{variables.cas_tab_csv_file_path}\Relative Volume\Legwise"
                )
                file_path += rf"\Leg_Wise\Unique_id_{unique_id}"

                if not os.path.exists(file_path):
                    os.makedirs(file_path)

                df_xxx.to_csv(
                    rf"{file_path}\Leg_{i+1}_Relative_Volume.csv", index=False
                )

        elif variables.flag_store_cas_tab_csv_files and last_n_minutes_lookback != None:

            for i, df_xxx in enumerate(all_data_frames):

                file_path = rf"{variables.cas_tab_csv_file_path}\Last N Minutes Fields\Legwise Volume"
                file_path += rf"\Leg_Wise\Unique_id_{unique_id}"

                if not os.path.exists(file_path):
                    os.makedirs(file_path)

                df_xxx.to_csv(
                    rf"{file_path}\Leg_{i+1}_Relative_Volume.csv", index=False
                )

        # Data not found for any leg
        is_data_frame_empty = False

        # If data is not present
        for i, historical_dataframe in enumerate(all_data_frames):
            if (
                historical_dataframe is None
                or len(historical_dataframe.index) == 0
                or historical_dataframe.empty
            ):
                is_data_frame_empty = True
                # Print to console
                if variables.flag_debug_mode:
                    print(f"Empty Data Frame : Unqiue ID {unique_id}")
                break

        # If any dataframe is empty can not compute the values
        if is_data_frame_empty:
            if last_n_minutes_lookback == None:

                # Dict
                local_map_unique_id_to_relative_volume_field[unique_id] = {
                    "Relative Volume": "N/A",
                    "Relative Volume Derivative": "N/A",
                    "Relative Volume on Positive Candles": "N/A",
                    "Relative Volume on Negative Candles": "N/A",
                    "Relative Volume on Lower Range": "N/A",
                    "Relative Volume on Higher Range": "N/A",
                }

            else:

                # Dict
                local_map_unique_id_to_last_n_minutes_field[unique_id] = {
                    "Relative Volume Last N Minutes": "N/A"
                }

            continue

        # Merging the data frame, inner join on time
        merged_df = merge_dataframe_inner_join_with_combo_net_volume_calculation(
            combo_obj, all_data_frames
        )

        # Save DF to CSV File
        if variables.flag_store_cas_tab_csv_files and last_n_minutes_lookback == None:

            # Saving dataframe to csv
            file_path = rf"{variables.cas_tab_csv_file_path}\Relative Volume\Merged"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            merged_df.to_csv(
                rf"{file_path}\Unique_Id_{unique_id}_Relative_Volume_all_legs_merged.csv",
                index=False,
            )

        elif variables.flag_store_cas_tab_csv_files and last_n_minutes_lookback != None:

            # Saving dataframe to csv
            file_path = rf"{variables.cas_tab_csv_file_path}\Last N Minutes Fields\Merged Volume"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            merged_df.to_csv(
                rf"{file_path}\Unique_Id_{unique_id}_Relative_Volume_all_legs_merged.csv",
                index=False,
            )

        # Create new DataFrame with desired columns
        combination_net_volume_dataframe = merged_df[
            [
                "Time",
                "Combination Volume",
            ]
        ].copy()

        # Try to divide historical data in two parts (today and old) for relative indicators
        try:
            # Create a new dataframe having the latest day available vlaues, and reset index
            latest_available_date = combination_net_volume_dataframe.iloc[-1][
                "Time"
            ].date()
            latest_day_dataframe = combination_net_volume_dataframe[
                combination_net_volume_dataframe["Time"].dt.date
                == latest_available_date
            ].copy()
            historical_data_except_current_day_dataframe = (
                combination_net_volume_dataframe[
                    combination_net_volume_dataframe["Time"].dt.date
                    < latest_available_date
                ].copy()
            )

            # Reset the index of dataframes
            latest_day_dataframe = latest_day_dataframe.reset_index(drop=True)
            historical_data_except_current_day_dataframe = (
                historical_data_except_current_day_dataframe.reset_index(drop=True)
            )

            # Checking if last n minute parameter is available
            if last_n_minutes_lookback != None:

                # Create a new dataframe having the latest day available values, and reset index
                previous_available_date = (
                    historical_data_except_current_day_dataframe.iloc[-1]["Time"].date()
                )
                previous_day_dataframe = historical_data_except_current_day_dataframe[
                    historical_data_except_current_day_dataframe["Time"].dt.date
                    == previous_available_date
                ].copy()
                historical_data_except_current_and_previous_day_dataframe = (
                    historical_data_except_current_day_dataframe[
                        historical_data_except_current_day_dataframe["Time"].dt.date
                        < previous_available_date
                    ].copy()
                )

                # Reset the index of dataframes
                previous_day_dataframe = previous_day_dataframe.reset_index(drop=True)
                historical_data_except_current_and_previous_day_dataframe = historical_data_except_current_and_previous_day_dataframe.reset_index(
                    drop=True
                )

                # Start Time and End Time for the Relative ATR
                start_time_of_time_slot = previous_day_dataframe.loc[
                    previous_day_dataframe.index[-1], "Time"
                ]
                end_time_of_time_slot = previous_day_dataframe.loc[
                    previous_day_dataframe.index[-1], "Time"
                ]

                try:

                    # Calculate relative volume
                    relative_volume = calculate_relative_volume(
                        unique_id,
                        previous_day_dataframe,
                        historical_data_except_current_and_previous_day_dataframe,
                        start_time_of_time_slot,
                        end_time_of_time_slot,
                        flag_last_n_minute_field=True,
                    )

                    # Store rel volumn in dict
                    local_map_unique_id_to_last_n_minutes_field[unique_id] = {
                        "Relative Volume Last N Minutes": relative_volume
                    }

                except Exception as e:

                    relative_volume = "N/A"

                    # Print to console
                    if variables.flag_debug_mode:

                        print(f"Exception in calculation of relative_volume, Exp: {e}")
            else:
                # Number of Candles in Latest Day Dataframe
                number_of_candles_since_day_open = len(latest_day_dataframe)

                # Start Time and End Time for the Relative ATR
                start_time_for_relative_volume = latest_day_dataframe.loc[0, "Time"]
                end_time_for_relative_volume = latest_day_dataframe.loc[
                    latest_day_dataframe.index[-1], "Time"
                ]

                # Subtract 15 minutes using Timedelta
                end_time_for_relative_volume_derivative = (
                    end_time_for_relative_volume
                    - pd.Timedelta(
                        minutes=variables.relative_volume_derivation_lookback_mins
                    )
                )

                # Calculate relative volume
                relative_volume_n_mins_back = calculate_relative_volume(
                    unique_id,
                    latest_day_dataframe,
                    historical_data_except_current_day_dataframe,
                    start_time_for_relative_volume,
                    end_time_for_relative_volume_derivative,
                )

                try:

                    # pd.options.mode.chained_assignment = None  # default='warn'
                    latest_day_dataframe_prices = prices_df_dict[unique_id][
                        "Latest Day"
                    ]
                    historical_data_except_current_day_dataframe_prices = (
                        prices_df_dict[unique_id]["Historic Data Except Current Day"]
                    )

                    latest_day_dataframe_prices = (
                        latest_day_dataframe_prices.reset_index(drop=True)
                    )
                    historical_data_except_current_day_dataframe_prices = (
                        historical_data_except_current_day_dataframe_prices.reset_index(
                            drop=True
                        )
                    )

                    # Merge column combination close & open from df1 into df2
                    merged_latst_day_volume_price_df = pd.concat(
                        [
                            latest_day_dataframe,
                            latest_day_dataframe_prices[
                                ["Combination Close", "Combination Open"]
                            ],
                        ],
                        axis=1,
                    )

                    # Merge column combination close & open from df1 into df2
                    merged_historic_days_volume_price_df = pd.concat(
                        [
                            historical_data_except_current_day_dataframe,
                            historical_data_except_current_day_dataframe_prices[
                                ["Combination Close", "Combination Open"]
                            ],
                        ],
                        axis=1,
                    )

                    # Get filterd latest day dataframe
                    latest_day_positive_candles_df = merged_latst_day_volume_price_df[
                        merged_latst_day_volume_price_df["Combination Close"]
                        > merged_latst_day_volume_price_df["Combination Open"]
                    ].copy()
                    latest_day_negative_candles_df = merged_latst_day_volume_price_df[
                        merged_latst_day_volume_price_df["Combination Close"]
                        < merged_latst_day_volume_price_df["Combination Open"]
                    ].copy()

                    # Get filtered historical dataframe
                    historical_data_except_current_day_dataframe_positive_candles_df = (
                        merged_historic_days_volume_price_df[
                            merged_historic_days_volume_price_df["Combination Close"]
                            > merged_historic_days_volume_price_df["Combination Open"]
                        ].copy()
                    )

                    historical_data_except_current_day_dataframe_negative_candles_df = (
                        merged_historic_days_volume_price_df[
                            merged_historic_days_volume_price_df["Combination Close"]
                            < merged_historic_days_volume_price_df["Combination Open"]
                        ].copy()
                    )

                    # Calculate relative volume on positive candles
                    relative_volume_on_positive_candles = calculate_relative_volume(
                        unique_id,
                        latest_day_positive_candles_df,
                        historical_data_except_current_day_dataframe_positive_candles_df,
                        start_time_for_relative_volume,
                        end_time_for_relative_volume,
                    )

                    # Calculate relative volume on negative candles
                    relative_volume_on_negative_candles = calculate_relative_volume(
                        unique_id,
                        latest_day_negative_candles_df,
                        historical_data_except_current_day_dataframe_negative_candles_df,
                        start_time_for_relative_volume,
                        end_time_for_relative_volume,
                    )

                    # Save DF to CSV File
                    if variables.flag_store_cas_tab_csv_files:

                        # Saving dataframe to csv
                        file_path = rf"{variables.cas_tab_csv_file_path}\Support Resistance And Relative Fields\Current Day Positive_Negative Candles Volume"

                        if not os.path.exists(file_path):
                            os.makedirs(file_path)

                        latest_day_positive_candles_df.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_volume_positive_candles.csv",
                            index=False,
                        )

                        latest_day_negative_candles_df.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_volume_negative_candles.csv",
                            index=False,
                        )

                        # Saving dataframe to csv
                        file_path = rf"{variables.cas_tab_csv_file_path}\Support Resistance And Relative Fields\Historical Days Except Current Day Positive Negative Candles Volume"

                        if not os.path.exists(file_path):
                            os.makedirs(file_path)

                        historical_data_except_current_day_dataframe_positive_candles_df.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_volume__positive_candles.csv",
                            index=False,
                        )

                        historical_data_except_current_day_dataframe_negative_candles_df.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_volume_negative_candles.csv",
                            index=False,
                        )

                except Exception as e:

                    # Set to N/A
                    relative_volume_on_positive_candles = "N/A"
                    relative_volume_on_negative_candles = "N/A"

                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Exception in getting positive and negative candles dataframe for relative volume, Exp: {e}"
                        )

                try:

                    # get lower and higher range df for prices
                    latest_day_lower_range_df_prices = prices_df_dict[unique_id][
                        "Latest Day Lower Range"
                    ]
                    latest_day_higher_range_df_prices = prices_df_dict[unique_id][
                        "Latest Day Higher Range"
                    ]
                    historical_data_except_current_day_dataframe_lower_range_df_prices = prices_df_dict[
                        unique_id
                    ][
                        "Historic Data Except Current Day Lower Range"
                    ]
                    historical_data_except_current_day_dataframe_higher_range_df_prices = prices_df_dict[
                        unique_id
                    ][
                        "Historic Data Except Current Day Higher Range"
                    ]

                    # reset index
                    latest_day_lower_range_df_prices = (
                        latest_day_lower_range_df_prices.reset_index(drop=True)
                    )
                    latest_day_higher_range_df_prices = (
                        latest_day_higher_range_df_prices.reset_index(drop=True)
                    )
                    historical_data_except_current_day_dataframe_lower_range_df_prices = historical_data_except_current_day_dataframe_lower_range_df_prices.reset_index(
                        drop=True
                    )
                    historical_data_except_current_day_dataframe_higher_range_df_prices = historical_data_except_current_day_dataframe_higher_range_df_prices.reset_index(
                        drop=True
                    )

                    # Filter the second DataFrame based on values in column  present in the first DataFrame
                    latest_day_dataframe_lower_range = (
                        latest_day_dataframe[
                            latest_day_dataframe["Time"].isin(
                                latest_day_lower_range_df_prices["Time"]
                            )
                        ]
                        .copy()
                        .reset_index(drop=True)
                    )

                    latest_day_dataframe_higher_range = (
                        latest_day_dataframe[
                            latest_day_dataframe["Time"].isin(
                                latest_day_higher_range_df_prices["Time"]
                            )
                        ]
                        .copy()
                        .reset_index(drop=True)
                    )

                    historical_data_except_current_day_dataframe_lower_range = (
                        historical_data_except_current_day_dataframe[
                            historical_data_except_current_day_dataframe["Time"].isin(
                                historical_data_except_current_day_dataframe_lower_range_df_prices[
                                    "Time"
                                ]
                            )
                        ]
                        .copy()
                        .reset_index(drop=True)
                    )

                    historical_data_except_current_day_dataframe_higher_range = (
                        historical_data_except_current_day_dataframe[
                            historical_data_except_current_day_dataframe["Time"].isin(
                                historical_data_except_current_day_dataframe_higher_range_df_prices[
                                    "Time"
                                ]
                            )
                        ]
                        .copy()
                        .reset_index(drop=True)
                    )

                    # Calculate relative volume on positive candles
                    relative_volume_on_lower_range = calculate_relative_volume(
                        unique_id,
                        latest_day_dataframe_lower_range,
                        historical_data_except_current_day_dataframe_lower_range,
                        start_time_for_relative_volume,
                        end_time_for_relative_volume,
                    )

                    # Calculate relative volume on negative candles
                    relative_volume_on_higher_range = calculate_relative_volume(
                        unique_id,
                        latest_day_dataframe_higher_range,
                        historical_data_except_current_day_dataframe_higher_range,
                        start_time_for_relative_volume,
                        end_time_for_relative_volume,
                    )
                    # print([relative_volume_on_lower_range,relative_volume_on_higher_range])
                    # Save DF to CSV File
                    if variables.flag_store_cas_tab_csv_files:

                        # Saving dataframe to csv
                        file_path = rf"{variables.cas_tab_csv_file_path}\Relative Fields in Range\Current Day Lower Higher Range Volume"

                        if not os.path.exists(file_path):
                            os.makedirs(file_path)

                        latest_day_dataframe_lower_range.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_volume_lower_range.csv",
                            index=False,
                        )

                        latest_day_dataframe_higher_range.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_volume_higher_range.csv",
                            index=False,
                        )

                        # Saving dataframe to csv
                        file_path = rf"{variables.cas_tab_csv_file_path}\Relative Fields in Range\Historical Days Except Current Day Lower Higher Range Volume"

                        if not os.path.exists(file_path):
                            os.makedirs(file_path)

                        historical_data_except_current_day_dataframe_lower_range.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_volume_lower_range.csv",
                            index=False,
                        )

                        historical_data_except_current_day_dataframe_higher_range.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_volume_higher_range.csv",
                            index=False,
                        )

                except Exception as e:

                    relative_volume_on_lower_range = "N/A"
                    relative_volume_on_higher_range = "N/A"

                    # Print to console
                    if variables.flag_debug_mode:
                        print(
                            f"Exception in getting positive and negative candles dataframe for relative volume, Exp: {e}"
                        )

                # Check flag indicating which candles to use either since start of day or current candle
                if not variables.flag_since_start_of_day_candles_for_relative_fields:

                    # Calculate relative volume
                    relative_volume_current = calculate_relative_volume(
                        unique_id,
                        latest_day_dataframe,
                        historical_data_except_current_day_dataframe,
                        start_time_for_relative_volume,
                        end_time_for_relative_volume,
                    )

                    # making start time slot for current candle
                    start_time_for_relative_volume = end_time_for_relative_volume

                    # Editing dataframe to have current candle only
                    latest_day_dataframe = latest_day_dataframe.tail(1)

                # Calculate relative volume
                relative_volume = calculate_relative_volume(
                    unique_id,
                    latest_day_dataframe,
                    historical_data_except_current_day_dataframe,
                    start_time_for_relative_volume,
                    end_time_for_relative_volume,
                )

                # Init
                relative_volume_derivative = "N/A"

                try:

                    # Check flag indicating which candles to use either since start of day or current candle
                    if (
                        not variables.flag_since_start_of_day_candles_for_relative_fields
                    ):

                        # calcualte relative volume derivative
                        relative_volume_derivative = (
                            relative_volume_current / relative_volume_n_mins_back
                        )

                        # round of value
                        relative_volume_derivative = round(
                            relative_volume_derivative, 4
                        )

                    else:

                        # calcualte relative volume derivative
                        relative_volume_derivative = (
                            relative_volume / relative_volume_n_mins_back
                        )

                        # round of value
                        relative_volume_derivative = round(
                            relative_volume_derivative, 4
                        )

                except Exception as e:

                    relative_volume_derivative = "N/A"

                    # Print to console
                    if variables.flag_debug_mode:

                        print(
                            f"Exception inside calculating relative volume derivative, Exp: {e}"
                        )

                # Assign values in dict
                local_map_unique_id_to_relative_volume_field[unique_id] = {
                    "Relative Volume": relative_volume,
                    "Relative Volume Derivative": relative_volume_derivative,
                    "Relative Volume on Positive Candles": relative_volume_on_positive_candles,
                    "Relative Volume on Negative Candles": relative_volume_on_negative_candles,
                    "Relative Volume on Lower Range": relative_volume_on_lower_range,
                    "Relative Volume on Higher Range": relative_volume_on_higher_range,
                }

        except Exception as e:

            # Print to console:
            if variables.flag_debug_mode:
                print(f"Could not compute the Relative volume. Exception {e}")

            continue

    # When last n minutes parameted not available
    if last_n_minutes_lookback == None:

        return local_map_unique_id_to_relative_volume_field

    # When last n minutes parameter is available
    elif last_n_minutes_lookback != None:

        return local_map_unique_id_to_last_n_minutes_field

# Method to manage all calculate indicator values
def update_price_based_relative_indicators_values(
    conid_list=None, unique_id_added=None
):
    """
    Rel Atr, Rel Chg
    """
    # local copy of 'unique_id_to_combo_obj'
    local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

    local_map_unique_id_to_price_and_volume_based_indicators = {}

    # Init
    duration_size = (
        f"{variables.support_resistance_and_relative_fields_look_back_days} D"
    )
    bar_size = variables.support_resistance_and_relative_fields_candle_size.value

    # Create a local copy of 'cas_map_con_id_to_action_type_and_combo_type'
    cas_coinds_for_fetching_historical_data = copy.deepcopy(
        variables.cas_map_con_id_to_action_type_and_combo_type
    )

    if conid_list != None:
        # Create a filtered dictionary using a dictionary comprehension
        cas_coinds_for_fetching_historical_data = {
            key: cas_coinds_for_fetching_historical_data[key] for key in conid_list
        }

        # local copy of 'unique_id_to_combo_obj'
        local_unique_id_to_combo_obj = {
            unique_id_added: local_unique_id_to_combo_obj[unique_id_added]
        }

    max_id = 0

    # Get local dict
    local_unique_id_to_combo_obj_loop_copy = copy.deepcopy(local_unique_id_to_combo_obj)

    # Iterate all combos
    for unique_id_combo in local_unique_id_to_combo_obj_loop_copy:

        # Init
        variables.map_unique_id_to_legs_unique_id[unique_id_combo] = {'Leg Unique Ids': [], 'Combo Obj List': []}

        # Get combo obj
        combo_obj = local_unique_id_to_combo_obj[unique_id_combo]

        # Get all legs
        all_legs = combo_obj.buy_legs + combo_obj.sell_legs

        # Iterate all legs
        for leg_obj in all_legs:
            max_id += 1

            list_of_tuple_of_values = [(max_id, leg_obj.action, leg_obj.sec_type, leg_obj.symbol, 'None', 'None',
                                        leg_obj.right, leg_obj.quantity,
                                        leg_obj.multiplier, leg_obj.exchange,
                                        leg_obj.trading_class, leg_obj.currency, leg_obj.con_id,
                                        leg_obj.primary_exchange, leg_obj.strike_price,
                                        leg_obj.expiry_date,)]

            # Create combination and check if there is any error
            combination_obj = create_combination(
                list_of_tuple_of_values,
                input_from_db=True,
                input_from_cas_tab=True,
            )

            # Append value
            variables.map_unique_id_to_legs_unique_id[unique_id_combo]['Leg Unique Ids'].append(max_id * -1)

            variables.map_unique_id_to_legs_unique_id[unique_id_combo]['Combo Obj List'].append(combination_obj)

            # Assign combo obj for leg values calcualtion
            local_unique_id_to_combo_obj[max_id * -1] = combination_obj

    # Requesting historical data and getting reqid  (ask, bid)
    map_conid_action_bar_size_to_req_id = (
        get_historical_data_for_price_based_relative_indicators(
            cas_coinds_for_fetching_historical_data, duration_size, bar_size
        )
    )

    # Computing all the price based relative indicators
    (
        map_unique_id_to_price_based_indicators,
        prices_df_dict,
    ) = calculate_all_the_price_based_relative_indicators(
        local_unique_id_to_combo_obj, map_conid_action_bar_size_to_req_id
    )

    # Getting Volume for all the combinations
    map_conid_action_bar_size_to_req_id_for_volume_data = (
        get_historical_volume_for_all_combinations(
            cas_coinds_for_fetching_historical_data, duration_size, bar_size
        )
    )

    # WE WANT ALL THE CALCULATED VALUES (NET VOLU STD1, )
    map_unique_id_to_volume_related_fields = calculate_volume_related_fields(
        local_unique_id_to_combo_obj,
        map_conid_action_bar_size_to_req_id_for_volume_data,
        prices_df_dict=prices_df_dict,
    )

    # Requesting historical data and getting reqid  (ask, bid)
    map_conid_action_bar_size_to_req_id = (
        get_historical_data_for_price_based_relative_indicators(
            cas_coinds_for_fetching_historical_data,
            "1 D",
            "1 min",
            flag_both_bid_ask=True,
        )
    )

    map_unique_id_to_bid_ask_based_indicators = calculate_bid_ask_indicators(
        local_unique_id_to_combo_obj,
        map_conid_action_bar_size_to_req_id,
        prices_df_dict,
    )

    # Calcualte volume magnet
    # Init
    duration_size = f"{variables.volume_magnet_final_lookback_days} D"
    bar_size = variables.volume_magnet_candle_size.value

    # Requesting historical data and getting reqid  (ask, bid)
    map_conid_action_bar_size_to_req_id = (
        get_historical_data_for_price_based_relative_indicators(
            cas_coinds_for_fetching_historical_data, duration_size, bar_size
        )
    )

    # Computing all the price based relative indicators
    map_unique_id_to_volume_magnet_indicators = calculate_volume_magnet_indicators(
        local_unique_id_to_combo_obj, map_conid_action_bar_size_to_req_id
    )

    # Getting last n minutes duration size
    last_n_minutes_fields_lookback_days = (
        f"{variables.last_n_minutes_fields_lookback_days} D"
    )

    # Get candle size
    last_n_minutes_fields_candle_size = (
        variables.last_n_minutes_fields_candle_size.value
    )

    # Get candle size in string format
    candle_size_split = last_n_minutes_fields_candle_size.split(" ")
    last_n_minutes_fields_lookback_mins = "N/A"

    # Get candle size in float format
    if candle_size_split[1] in ["mins", "min"]:

        # Get past n minutes lookback in integer format
        last_n_minutes_fields_lookback_mins = int(float(candle_size_split[0]))

    else:

        # Get past n minutes lookback in integer format
        last_n_minutes_fields_lookback_mins = int(60 * float(candle_size_split[0]))

    # Requesting historical data and getting reqid  (ask, bid)
    map_conid_action_bar_size_to_req_id = (
        get_historical_data_for_price_based_relative_indicators(
            cas_coinds_for_fetching_historical_data,
            last_n_minutes_fields_lookback_days,
            last_n_minutes_fields_candle_size,
        )
    )

    # Computing all the price based relative indicators for last n minutes in lookback days
    map_unique_id_to_price_based_indicators_for_last_n_minutes = (
        calculate_all_the_price_based_relative_indicators(
            local_unique_id_to_combo_obj,
            map_conid_action_bar_size_to_req_id,
            last_n_minutes_lookback=last_n_minutes_fields_lookback_mins,
        )
    )

    # Getting Volume for all the combinations
    map_conid_action_bar_size_to_req_id_for_volume_data = (
        get_historical_volume_for_all_combinations(
            cas_coinds_for_fetching_historical_data,
            last_n_minutes_fields_lookback_days,
            last_n_minutes_fields_candle_size,
        )
    )

    # WE WANT ALL THE CALCULATED relative volume for last n minutes in lookback days
    map_unique_id_to_volume_related_fields_for_last_n_minutes = (
        calculate_volume_related_fields(
            local_unique_id_to_combo_obj,
            map_conid_action_bar_size_to_req_id_for_volume_data,
            last_n_minutes_lookback=last_n_minutes_fields_lookback_mins,
        )
    )

    # Get Common unique ids from price fields and volume fields dictionaries
    unique_ids_in_dict = set(map_unique_id_to_price_based_indicators.keys()) & set(
        map_unique_id_to_volume_related_fields.keys()
    )

    # Merger price related and volume related fields dictionaries
    for unique_id in unique_ids_in_dict:
        local_map_unique_id_to_price_and_volume_based_indicators[unique_id] = {}
        local_map_unique_id_to_price_and_volume_based_indicators[unique_id].update(
            map_unique_id_to_price_based_indicators[unique_id]
        )
        local_map_unique_id_to_price_and_volume_based_indicators[unique_id].update(
            map_unique_id_to_volume_related_fields[unique_id]
        )
        local_map_unique_id_to_price_and_volume_based_indicators[unique_id].update(
            map_unique_id_to_price_based_indicators_for_last_n_minutes[unique_id]
        )
        local_map_unique_id_to_price_and_volume_based_indicators[unique_id].update(
            map_unique_id_to_volume_related_fields_for_last_n_minutes[unique_id]
        )
        local_map_unique_id_to_price_and_volume_based_indicators[unique_id].update(
            map_unique_id_to_bid_ask_based_indicators[unique_id]
        )
        local_map_unique_id_to_price_and_volume_based_indicators[unique_id].update(
            map_unique_id_to_volume_magnet_indicators[unique_id]
        )

        variables.map_unique_id_to_support_resistance_and_relative_fields[
            unique_id
        ] = local_map_unique_id_to_price_and_volume_based_indicators[unique_id]

    # Print to console
    if variables.flag_debug_mode:
        print(f"\nIntra-Day")

    # Setting updated value in the variables dict
    # variables.map_unique_id_to_support_resistance_and_relative_fields = local_map_unique_id_to_price_and_volume_based_indicators
