import enum
from com import *
from com.prices import *
from com.variables import variables
from com.hv_calculation import *
from com.significant_levels_support_resistance import *
import numpy as np
from com.cas_pop_up_window_related_columns import *
from com.calc_weighted_change import *
from com.high_low_cal_helper import *


# Merge dataframe for volume calculation in trade level RM check
def merge_dataframe_for_volume_trade_rm_check(combo_obj, all_data_frames):
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
            merged_df, df_ith, on="Time", how="inner", suffixes=(f"", f" {i + 1}")
        )

    # Dropping nan values, if any
    merged_df = merged_df.dropna()

    # Creating Columns for merged dataframe
    merged_df_columns = ["Time"]

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

    # Volume with leg
    for i in range(len(all_data_frames)):
        merged_df_columns.append(f"Volume {i + 1}")

    # Setting columns in merged_df
    merged_df.columns = merged_df_columns

    # Init list to store total volumes for leg
    list_of_sum_of_volume = []

    # Iterate volumen columns
    for indx, column_name in enumerate(merged_df_columns[1:]):
        try:
            # Divide it by factor
            merged_df[column_name] = merged_df[column_name].apply(
                lambda x: float(x) / factors[indx]
            )

            # append total volume of leg in list
            list_of_sum_of_volume.append(merged_df[column_name].sum())

        except Exception as e:
            # Print to console
            if variables.flag_debug_mode:
                print(f"Inside getting total volume for leg, Exp: {e}")

    return list_of_sum_of_volume


# Method to validate volume related condition
def evaluate_volume_related_check(local_unique_id_to_combo_obj, map_conid_to_req_id):
    # Dict
    local_map_unique_id_to_volume_check = {}

    # Iterate unique ids
    for unique_id, combo_obj in local_unique_id_to_combo_obj.items():
        # Dict
        local_map_unique_id_to_volume_check[unique_id] = {"Volume Check": True}

        # Get leg objects
        buy_legs = combo_obj.buy_legs
        sell_legs = combo_obj.sell_legs
        all_legs = buy_legs + sell_legs

        # list of request_id
        req_id_list = []

        # Getting all the reqId for which the historical data was requested
        for leg in all_legs:
            # getting conid
            con_id = leg.con_id
            req_id = map_conid_to_req_id[con_id]
            req_id_list.append(req_id)

        # Getting all the Dataframes for the legs, Process Data,
        all_data_frames = [
            variables.map_req_id_to_historical_data_dataframe[req_id]
            for req_id in req_id_list
        ]

        # Save DF to CSV File
        if variables.flag_store_cas_tab_csv_files:
            for i, df_xxx in enumerate(all_data_frames):
                file_path = (
                    rf"{variables.cas_tab_csv_file_path}\Trade RM Check Volume\Legwise"
                )
                file_path += rf"\Leg_Wise\Unique_id_{unique_id}"

                if not os.path.exists(file_path):
                    os.makedirs(file_path)

                df_xxx.to_csv(
                    rf"{file_path}\Leg_{i + 1}_Trade_RM_Check_Volume.csv", index=False
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
            local_map_unique_id_to_volume_check[unique_id] = {"Volume Check": False}

        # Merging the data frame, inner join on time
        list_of_sum_of_volume = merge_dataframe_for_volume_trade_rm_check(
            combo_obj, all_data_frames
        )

        # Check if all values are greater than threshold
        rm_check_value = all(
            volume_value > variables.volume_threshold_trade_rm_check
            for volume_value in list_of_sum_of_volume
        )

        # assign value in dict
        local_map_unique_id_to_volume_check[unique_id] = {
            "Volume Check": rm_check_value
        }

    return local_map_unique_id_to_volume_check


# Method to validate bid ask spread condition
def evaualte_bid_ask_spread_rm_check(local_unique_id_to_combo_obj):
    # Dict
    local_map_unique_id_to_bid_ask_spread_check = {}

    # Iterate unique ids
    for unique_id, combo_obj in local_unique_id_to_combo_obj.items():
        try:
            # Init
            local_map_unique_id_to_bid_ask_spread_check[unique_id] = {
                "Bid Ask Spread Check": False
            }

            # Buy legs and Sell legs
            buy_legs = combo_obj.buy_legs
            sell_legs = combo_obj.sell_legs

            # init list of bid ask spread for legs
            bid_ask_spread_pcnt_list = []

            # Processing "Buy" Legs to calculate prices
            for leg_obj in buy_legs:
                # Get con id
                con_id = leg_obj.con_id

                # get req id
                req_id = variables.con_id_to_req_id_dict[con_id]

                # Get bid price and ask price
                bid_price, ask_price = (
                    variables.bid_price[req_id],
                    variables.ask_price[req_id],
                )

                # calcualte spread %
                spread_pcnt = (ask_price - bid_price) / ((ask_price + bid_price) / 2)

                bid_ask_spread_pcnt_list.append(spread_pcnt)

            # Processing "Buy" Legs to calculate prices
            for leg_obj in sell_legs:
                # Get con id
                con_id = leg_obj.con_id

                # get req id
                req_id = variables.con_id_to_req_id_dict[con_id]

                # Get bid price and ask price
                bid_price, ask_price = (
                    variables.bid_price[req_id],
                    variables.ask_price[req_id],
                )

                # calcualte spread %
                spread_pcnt = (ask_price - bid_price) / ((ask_price + bid_price) / 2)

                bid_ask_spread_pcnt_list.append(spread_pcnt)
            # print([bid_ask_spread_pcnt_list, unique_id])
            # Check if all values are greater than threshold
            rm_check_value = all(
                bid_ask_pcnt_value < variables.bid_ask_spread_threshold_trade_rm_check
                for bid_ask_pcnt_value in bid_ask_spread_pcnt_list
            )

            # assign value n dict
            local_map_unique_id_to_bid_ask_spread_check[unique_id] = {
                "Bid Ask Spread Check": rm_check_value
            }

        except Exception as e:
            # assign value n dict
            local_map_unique_id_to_bid_ask_spread_check[unique_id] = {
                "Bid Ask Spread Check": False
            }

    return local_map_unique_id_to_bid_ask_spread_check


# Method to calculate bid ask size condition
def evaluate_bid_ask_qty_rm_check_for_all_combinations(local_unique_id_to_combo_obj):
    # Init dict
    local_map_unique_id_to_bid_ask_qty_check = {}

    for unique_id, combo_obj in local_unique_id_to_combo_obj.items():
        try:
            # Init
            local_map_unique_id_to_bid_ask_qty_check[unique_id] = {
                "Bid Ask Qty Check": False
            }

            # Buy legs and Sell legs
            buy_legs = combo_obj.buy_legs
            sell_legs = combo_obj.sell_legs

            # Init list
            bid_ask_qty_list = []

            # Processing "Buy" Legs to calculate qty
            for leg_obj in buy_legs:
                # get conid
                con_id = leg_obj.con_id

                # get req id
                req_id = variables.con_id_to_req_id_dict[con_id]

                # get ask qty for buy legs
                ask_size = variables.ask_size[req_id]

                if leg_obj.sec_type == "STK":
                    ask_size *= 100

                # append qty to list
                bid_ask_qty_list.append(ask_size)

            # Processing "Buy" Legs to calculate prices
            for leg_obj in sell_legs:
                # get conid
                con_id = leg_obj.con_id

                # get req id
                req_id = variables.con_id_to_req_id_dict[con_id]

                # get bid qty for sell legs
                bid_size = variables.bid_size[req_id]

                if leg_obj.sec_type == "STK":
                    bid_size *= 100

                bid_ask_qty_list.append(bid_size)

            # Check if all values are greater than threshold
            rm_check_value = all(
                bid_ask_size_value > variables.bid_ask_qty_threshold_trade_rm_check
                for bid_ask_size_value in bid_ask_qty_list
            )

            # assign value n dict
            local_map_unique_id_to_bid_ask_qty_check[unique_id] = {
                "Bid Ask Qty Check": rm_check_value
            }

        except Exception as e:
            # assign value n dict
            local_map_unique_id_to_bid_ask_qty_check[unique_id] = {
                "Bid Ask Qty Check": False
            }

    return local_map_unique_id_to_bid_ask_qty_check


# Method to validate combine result of all conditions in trade level RM check
def trade_level_rm_check_func():
    # local copy of 'unique_id_to_combo_obj'
    local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

    local_map_unique_id_to_price_and_volume_based_indicators = {}

    # Init
    duration_size = f"{variables.trade_level_rm_check_volume_lookback_mins * 60} S"
    bar_size = variables.trade_level_rm_check_volume_candle_size.value

    # Create a local copy of 'cas_map_con_id_to_action_type_and_combo_type'
    cas_coinds_for_fetching_historical_data = copy.deepcopy(
        variables.cas_map_con_id_to_action_type_and_combo_type
    )

    # Getting Volume for all the combinations
    map_conid_action_bar_size_to_req_id_for_volume_data = (
        get_historical_volume_for_all_combinations(
            cas_coinds_for_fetching_historical_data, duration_size, bar_size
        )
    )

    # all unique ids volume rm checks
    map_unique_id_to_volume_rm_check = evaluate_volume_related_check(
        local_unique_id_to_combo_obj,
        map_conid_action_bar_size_to_req_id_for_volume_data,
    )

    # all unique ids bid ask rm checks
    map_unique_id_to_bid_ask_spread_rm_check = evaualte_bid_ask_spread_rm_check(
        local_unique_id_to_combo_obj
    )

    # Get bid size and ask size rm checks
    map_unique_id_to_bid_ask_qty_check = (
        evaluate_bid_ask_qty_rm_check_for_all_combinations(local_unique_id_to_combo_obj)
    )

    # Init dict
    map_unique_id_to_rm_check_value = {}

    # Iterate unique ids
    for unique_id, combo_obj in local_unique_id_to_combo_obj.items():
        try:
            # check if user input is AND
            if variables.flag_rm_checks_trade_volume_and_or == "AND":
                map_unique_id_to_rm_check_value[unique_id] = (
                    map_unique_id_to_bid_ask_spread_rm_check[unique_id][
                        "Bid Ask Spread Check"
                    ]
                    and (
                        map_unique_id_to_volume_rm_check[unique_id]["Volume Check"]
                        and map_unique_id_to_bid_ask_qty_check[unique_id][
                            "Bid Ask Qty Check"
                        ]
                    )
                )

            # check if user input is OR
            elif variables.flag_rm_checks_trade_volume_and_or == "OR":
                map_unique_id_to_rm_check_value[unique_id] = (
                    map_unique_id_to_bid_ask_spread_rm_check[unique_id][
                        "Bid Ask Spread Check"
                    ]
                    and (
                        map_unique_id_to_volume_rm_check[unique_id]["Volume Check"]
                        or map_unique_id_to_bid_ask_qty_check[unique_id][
                            "Bid Ask Qty Check"
                        ]
                    )
                )

            else:
                # set value to false
                map_unique_id_to_rm_check_value[unique_id] = False

            # save details for trade rm check
            variables.map_unique_id_to_trade_rm_check_details[unique_id] = {
                "Bid Ask Spread Check": map_unique_id_to_bid_ask_spread_rm_check[
                    unique_id
                ]["Bid Ask Spread Check"],
                "Volume Check": map_unique_id_to_volume_rm_check[unique_id][
                    "Volume Check"
                ],
                "Bid Ask Qty Check": map_unique_id_to_bid_ask_qty_check[unique_id][
                    "Bid Ask Qty Check"
                ],
            }

        except Exception as e:
            # set value to false
            map_unique_id_to_rm_check_value[unique_id] = False

            # Print to console
            if variables.flag_debug_mode:
                print(f"Inside evaluating trade level RM check, Exp: {e}")

    variables.flag_trade_level_rm_checks = map_unique_id_to_rm_check_value
