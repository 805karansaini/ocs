"""
Created on 14-Apr-2023

@author: Karan
"""
import copy
import enum
from com import *
from com.prices import *
from com.variables import variables
from com.hv_calculation import *
from com.significant_levels_support_resistance import *
import numpy as np
from com.cas_pop_up_window_related_columns import *
from com.calc_weighted_change import *
from com.combination_helper import create_combination
from datetime import datetime


# Enums the hv_methods(historical volatility)
class HVMethod(enum.Enum):
    STANDARD_DEVIATION = 1
    PARKINSON_WITH_GAP = 2
    PARKINSON_WITHOUT_GAP = 3
    ATR = 4


class HighLowCalculator(object):
    def __init__(self):
        pass

    # Manage long erm values calculation
    def update_long_term_values(self, conid_list=None, unique_id_added=None):

        # local copy of 'unique_id_to_combo_obj'
        local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

        # local copy of 'unique_id_to_cas_legs_combo' for which the correlation is required
        local_cas_unique_id_to_combo_obj = copy.deepcopy(
            variables.cas_unique_id_to_combo_obj
        )

        # Info 'cas_coinds_for_fetching_historical_data' contains dict {coind : {BUY : 1H:x, 1D:y ,  SELL: 1H:z, 1D:z1} }
        # Creating a local copy of 'cas_map_con_id_to_action_type_and_combo_type'
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

            local_cas_unique_id_to_combo_obj = {}

        max_id = 0

        local_unique_id_to_combo_obj_loop_copy = copy.deepcopy(local_unique_id_to_combo_obj)

        # create combo objects for legs separately to calculate values for legs
        for unique_id_combo in local_unique_id_to_combo_obj_loop_copy:

            variables.map_unique_id_to_legs_unique_id[unique_id_combo] = {'Leg Unique Ids': [], 'Combo Obj List': []}

            combo_obj = local_unique_id_to_combo_obj[unique_id_combo]

            all_legs = combo_obj.buy_legs + combo_obj.sell_legs

            for leg_obj in all_legs:
                max_id += 1

                list_of_tuple_of_values = [(max_id, leg_obj.action, leg_obj.sec_type, leg_obj.symbol, 'None', 'None', leg_obj.right, leg_obj.quantity,
                 leg_obj.multiplier, leg_obj.exchange,
                 leg_obj.trading_class, leg_obj.currency, leg_obj.con_id, leg_obj.primary_exchange, leg_obj.strike_price,
                 leg_obj.expiry_date,)]

                # Create combination and check if there is any error
                combination_obj = create_combination(
                    list_of_tuple_of_values,
                    input_from_db=True,
                    input_from_cas_tab=True,
                )

                variables.map_unique_id_to_legs_unique_id[unique_id_combo]['Leg Unique Ids'].append(max_id * -1)

                variables.map_unique_id_to_legs_unique_id[unique_id_combo]['Combo Obj List'].append(combination_obj)

                local_unique_id_to_combo_obj[max_id * -1] = combination_obj



        # Creating a local copy of 'cas_conditional_legs_map_con_id_to_action_type_and_combo_type'
        cas_conids_for_correlation = copy.deepcopy(
            variables.cas_conditional_legs_map_con_id_to_action_type_and_combo_type
        )

        # Creating a single dict for which the N-Day historical data is required
        for key, val in cas_conids_for_correlation.items():
            if key in cas_coinds_for_fetching_historical_data:

                # Adding Values
                for action_ in ["BUY", "SELL"]:
                    for candle_ in [
                        "1H",
                    ]:
                        cas_coinds_for_fetching_historical_data[key][action_][
                            candle_
                        ] += cas_conids_for_correlation[key][action_][candle_]

            else:
                cas_coinds_for_fetching_historical_data[key] = val

        # xxx Coind cas_coinds_for_fetching_historical_data = {Coind COmbination} local_unique_id_to_combo_obj UID, COids Dict local_cas_unique_id_to_combo_obj[xax
        # Requesting historical data and getting 'map_conid_action_bar_size_to_req_id' [coind][action][bar] = reqId
        map_conid_action_bar_size_to_req_id = self.get_long_term_values(
            cas_coinds_for_fetching_historical_data
        )
        map_conid_action_bar_size_to_req_id = copy.deepcopy(map_conid_action_bar_size_to_req_id)

        # Getting Highest and Lowest Price of combo for N-Days (cas_number_of_days)
        map_unique_id_to_high_low = self.get_ndays_highest_lowest_price(
            local_unique_id_to_combo_obj,
            map_conid_action_bar_size_to_req_id,
            local_cas_unique_id_to_combo_obj,
        )

        # Print to console
        if variables.flag_debug_mode:
            print("\nLongTerm")

        # Updating Long Term Value in DB
        for unique_id_, values in map_unique_id_to_high_low.items():

            # Print to console
            if variables.flag_debug_mode:
                print(unique_id_, " : ", values)

            try:

                n_day_high = values["N-Day High"]
                n_day_low = values["N-Day Low"]

            except Exception as e:

                n_day_high = "N/A"
                n_day_low = "N/A"

            # Update Values in class variable
            variables.map_unique_id_to_n_day_high_low[unique_id_] = values

        # Update the last updated time of longterm values
        update_last_longterm_or_intraday_updated_time(is_intraday=False)

    # Method to get long term values
    def get_long_term_values(self, cas_coinds_for_fetching_historical_data):

        # Info 'cas_coinds_for_fetching_historical_data' contains dict {coind : {BUY : 1H 1D ,  SELL: 1H 1D} }

        # Duration String, user input max(cas_number_of_days and atr)
        duration_for_historical_data = max(
            variables.cas_number_of_days, variables.atr_number_of_days
        )



        # string for ibkr reqHistoricalData
        duration_size = f"{duration_for_historical_data} D"

        # Map of [conid][action][bar_size] = req_id
        map_conid_action_bar_size_to_req_id = {}

        # List of all request ids
        req_id_list = []

        # To update long term values we need Daily Candles for which we need '1D' '1H' data.
        for conid, sub_info_dict in cas_coinds_for_fetching_historical_data.items():

            # Get Contract for conId
            contract = variables.map_con_id_to_contract[conid]

            # Create dict with conid as key
            if conid not in map_conid_action_bar_size_to_req_id:
                map_conid_action_bar_size_to_req_id[conid] = {}

            for action, sub_values in sub_info_dict.items():

                # Create dict with conid as key
                if action not in map_conid_action_bar_size_to_req_id[conid]:
                    map_conid_action_bar_size_to_req_id[conid][action] = {}


                # Get data for bar_size, if leg is active in all combinations
                for bar_size, sub_val in sub_values.items():

                    if sub_val > 0:

                        # Getting req_id from CAS APP
                        reqId = variables.cas_app.nextorderId
                        variables.cas_app.nextorderId += 1

                        # Create dict with bar_size as key if not already present, Here Bar Size is '1 H' and '1 D'
                        if (
                            bar_size
                            not in map_conid_action_bar_size_to_req_id[conid][action]
                        ):
                            map_conid_action_bar_size_to_req_id[conid][action][
                                bar_size
                            ] = 0

                        # Map Historical Data ReqId to the dict
                        map_conid_action_bar_size_to_req_id[conid][action][
                            bar_size
                        ] = reqId

                        # append reqid it to the list, will be used to check when all the data is available
                        req_id_list.append(reqId)

                        # candle / bar size for reqHistoricalData
                        bar_size = "1 hour" if bar_size == "1H" else "1 Day"

                        # What to Show for reqHistoricalData
                        if action == "BUY":
                            what_to_show = "ASK"
                        else:
                            what_to_show = "BID"
                        # print(reqId)
                        # Get the historical data
                        request_historical_price_data_for_contract(
                            contract,
                            bar_size,
                            duration_size,
                            what_to_show,
                            req_id=reqId,
                            cas_app=True,
                        )

        # Counter for wait
        counter = 0

        # Keep Waiting for data till  'cas_wait_time_for_historical_data' time
        while variables.cas_wait_time_for_historical_data > (
            counter * variables.sleep_time_waiting_for_tws_response
        ):

            # dict_mkt_end = variables.req_mkt_data_end
            # dicterr_msg = variables.req_error
            #
            # merged_dict = {}
            #
            # for key in set(dict_mkt_end.keys()) | set(dicterr_msg.keys()):
            #     if key in dict_mkt_end and key in dicterr_msg:
            #         merged_dict[key] = dict_mkt_end[key] or dicterr_msg[key]
            #     elif key in dict_mkt_end:
            #         merged_dict[key] = dict_mkt_end[key]
            #     else:
            #         merged_dict[key] = dicterr_msg[key]
            #
            # # If reqHistorical Data ended for all the reqId
            # if all([merged_dict[req_id] for req_id in req_id_list]):
            #     break

            # KARAN CHANGED IT - TODO - 20231027
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

        return map_conid_action_bar_size_to_req_id

    # Meethod to get highest and lowest in n days
    def get_ndays_highest_lowest_price(
        self,
        local_unique_id_to_combo_obj,
        map_conid_action_bar_size_to_req_id,
        local_cas_unique_id_to_combo_obj,
    ):

        # Dictionary maps unique_id to long_term_high_low
        # variables.map_unique_id_to_long_term_high_low = {}
        try:
            # Duration String, user input max(cas_number_of_days and atr)
            duration_for_historical_data = max(
                variables.cas_number_of_days, variables.atr_number_of_days
            )

            # string for ibkr reqHistoricalData
            duration_size = f"{duration_for_historical_data} D"

            # Getting historical data for index (SPY or QQQ) for beta calculation
            index_dataframe = self.historical_data_for_index(
                duration_size, "1 hour"
            )  # candles size will be strictly 1 hour

            # Rename columns
            index_dataframe = index_dataframe.rename(
                columns={"Open": "Combination Open", "Close": "Combination Close"}
            )
            index_dataframe = (
                self.group_dataframe_by_time_and_create_1d_candle_first_open_last_close(
                    index_dataframe.copy()
                )
            )

            # Sequence of index dataframe columns
            index_df_columns = ["Date", "Combination Open", "Combination Close"]

            # Rearrange columns
            index_dataframe = index_dataframe[index_df_columns]

        except Exception as e:
            index_dataframe = pd.DataFrame()
            if variables.flag_debug_mode:
                print(f"Error inside getting index historical data df, is {e}")

        # Process unique Id one by one
        for unique_id, combo_obj in local_unique_id_to_combo_obj.items():

            # Creating a sub dictionary
            variables.map_unique_id_to_long_term_high_low[unique_id] = {}

            # Getting bar size according to combo_obj (1D or 1H)
            all_data_frames = (
                self.get_the_dataframe_that_contains_historical_data_for_combo(
                    combo_obj, map_conid_action_bar_size_to_req_id
                )
            )

            # Save DF to CSV File
            if variables.flag_store_cas_tab_csv_files:

                # Save all DF to CSV
                for i, df_nday_legwise in enumerate(all_data_frames):

                    file_path = rf"{variables.cas_tab_csv_file_path}\N_Day\LegWise\Unique_id_{unique_id}"

                    if not os.path.exists(file_path):
                        os.makedirs(file_path)

                    df_nday_legwise.to_csv(rf"{file_path}\Leg_{i+1}.csv", index=False)

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
                        print(f"Empty Dataframe for Unique ID: {unique_id}")
                    break

            # Set Values to N/A for Unique ID
            if is_data_frame_empty:
                variables.map_unique_id_to_long_term_high_low[unique_id] = {
                    "ATR": "N/A",
                    "N-Day High": "N/A",
                    "N-Day Low": "N/A",
                    "Close Price": "N/A",
                    "Correlation": "N/A",
                    "Last Day Close Price For Legs": "N/A",
                    "Beta": "N/A",
                    "Avg chg In Price For Last N days": "N/A",
                }
                continue

            # Merging the data frame, inner join on time
            merged_df = self.merge_dataframe_inner_join_with_combo_price_calculation(
                combo_obj, all_data_frames
            )

            # Save DF to CSV File
            if variables.flag_store_cas_tab_csv_files:

                # Saving dataframe to csv
                file_path = rf"{variables.cas_tab_csv_file_path}\N_Day\Merged"

                if not os.path.exists(file_path):
                    os.makedirs(file_path)

                merged_df.to_csv(
                    rf"{file_path}\Unique_Id_{unique_id}_N_Day_all_legs_merged.csv",
                    index=False,
                )

            # Get last day close values
            if variables.flag_weighted_change_in_price:
                last_day_close_price_for_leg_list = get_last_day_close_for_each_leg(
                    merged_df, combo_obj
                )
            else:
                last_day_close_price_for_leg_list = "N/A"

            # Create new DataFrame with desired columns
            combination_price_dataframe = merged_df[
                ["Time", "Combination Open", "Combination Close"]
            ].copy()

            combination_price_dataframe_for_beta = (
                self.group_dataframe_by_time_and_create_1d_candle_first_open_last_close(
                    combination_price_dataframe.copy()
                )
            )

            combination_price_dataframe_for_avg_chg_in_price = (
                combination_price_dataframe_for_beta.copy()
            )

            try:

                # check length of df
                if len(combination_price_dataframe_for_avg_chg_in_price) < 2:
                    avg_change_in_price_for_n_days = "N/A"
                else:

                    # calcualte avg change in price for n days
                    combination_price_dataframe_for_avg_chg_in_price[
                        "Combination Close Change"
                    ] = combination_price_dataframe_for_avg_chg_in_price[
                        "Combination Close"
                    ] - combination_price_dataframe_for_avg_chg_in_price[
                        "Combination Close"
                    ].shift(
                        1
                    )
                    avg_change_in_price_for_n_days = (
                        combination_price_dataframe_for_avg_chg_in_price[
                            "Combination Close Change"
                        ].mean()
                    )

                # Save DF to CSV File (HV) Export data-frame to csv file
                if variables.flag_store_cas_tab_csv_files:

                    file_path = rf"{variables.cas_tab_csv_file_path}\Bid Ask Related Columns\Average Change In Price"

                    if not os.path.exists(file_path):
                        os.makedirs(file_path)

                    # Saving CSV
                    combination_price_dataframe_for_avg_chg_in_price.to_csv(
                        rf"{file_path}\{unique_id}_avg_change_in_prices.csv",
                        index=False,
                    )

            except Exception as e:
                avg_change_in_price_for_n_days = "N/A"
                if variables.flag_debug_mode:
                    print(
                        f"Error inside calculating avvg change in price for n days value for bid -ask indicatoris, is {e}"
                    )

            try:
                # Calculating Beta value for cas table
                beta_value = self.calculate_beta_value(
                    unique_id,
                    index_dataframe,
                    combination_price_dataframe_for_beta.copy(),
                )

            except Exception as e:
                beta_value = "N/A"
                if variables.flag_debug_mode:
                    print(f"Error inside calculating beta value, is {e}")

            # if we have cas legs calculate the Correlation
            if unique_id in local_cas_unique_id_to_combo_obj:

                # Cas Combo Object
                cas_combo_object = local_cas_unique_id_to_combo_obj[unique_id]

                # Getting All dataframes containing the historical data of cas legs
                cas_all_data_frames = (
                    self.get_the_dataframe_that_contains_historical_data_for_combo(
                        cas_combo_object, map_conid_action_bar_size_to_req_id
                    )
                )

                # Save DF to CSV File
                if variables.flag_store_cas_tab_csv_files:

                    # Save all DF to CSV
                    for i, df_nday_cas_legwise in enumerate(all_data_frames):

                        file_path = rf"{variables.cas_tab_csv_file_path}\N_Day\CASLegsLegWise\Unique_id_{unique_id}"

                        if not os.path.exists(file_path):
                            os.makedirs(file_path)

                        df_nday_cas_legwise.to_csv(
                            rf"{file_path}\Leg_{i+1}.csv", index=False
                        )

                # Data not found for any leg
                is_cas_data_frame_empty = False

                # If data is not present
                for i, cas_historical_dataframe in enumerate(cas_all_data_frames):
                    if (
                        cas_historical_dataframe is None
                        or len(cas_historical_dataframe.index) == 0
                        or cas_historical_dataframe.empty
                    ):
                        is_cas_data_frame_empty = True

                        # Print to console
                        if variables.flag_debug_mode:
                            print(f"Empty CAS Dataframe for Unique ID: {unique_id}")
                        break

                # Set Correlation to N/A for Unique ID
                if is_cas_data_frame_empty:
                    variables.map_unique_id_to_long_term_high_low[unique_id] = {
                        "Correlation": "N/A"
                    }

                else:

                    # Merging the data frame, inner join on time
                    cas_merged_df = (
                        self.merge_dataframe_inner_join_with_combo_price_calculation(
                            cas_combo_object, cas_all_data_frames
                        )
                    )

                    # Save DF to CSV File
                    if variables.flag_store_cas_tab_csv_files:

                        file_path = rf"{variables.cas_tab_csv_file_path}\N_Day\CASLegsMerged\Unique_id_{unique_id}"

                        if not os.path.exists(file_path):
                            os.makedirs(file_path)

                        cas_merged_df.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_N_Day_all_cas_legs_merged.csv",
                            index=False,
                        )

                    # Create new DataFrame with desired columns
                    cas_combination_price_dataframe = cas_merged_df[
                        ["Time", "Combination Open", "Combination Close"]
                    ].copy()

                    # Calculate the correlation
                    correlation = self.calculate_correlation_for_cas_unique_ids(
                        unique_id,
                        combination_price_dataframe,
                        cas_combination_price_dataframe,
                    )

            # if unique Id not in local_cas_unique_id_to_combo_obj
            else:
                correlation = None

            # Calculate the ATR for combination
            (
                calculated_atr,
                last_close_price,
            ) = self.calculate_combo_atr_and_last_close_price(
                unique_id,
                combination_price_dataframe,
            )

            high = None
            low = None

            # Getting Min, Max value from the DataFrame
            for i, row in combination_price_dataframe.iterrows():

                # Open and Close Prices of combination
                open_price = row["Combination Open"]
                close_price = row["Combination Close"]

                # Combination High
                if (high == None) or close_price > high:
                    high = close_price

                # Combination Low
                if (low == None) or close_price < low:
                    low = close_price

            # Format value 2 decimal
            high = "N/A" if high == None else int(high * 100) / 100
            low = "N/A" if low == None else int(low * 100) / 100
            calculated_atr = (
                "N/A" if calculated_atr == None else int(calculated_atr * 100) / 100
            )  # Calculated from the function
            last_close_price = (
                "N/A" if last_close_price == None else int(last_close_price * 100) / 100
            )  # Calculated from the function
            correlation = "N/A" if correlation == None else correlation

            variables.map_unique_id_to_long_term_high_low[unique_id] = {
                "ATR": calculated_atr,
                "N-Day High": high,
                "N-Day Low": low,
                "Close Price": last_close_price,
                "Correlation": correlation,
                "Last Day Close Price For Legs": last_day_close_price_for_leg_list,
                "Beta": beta_value,
                "Avg chg In Price For Last N days": avg_change_in_price_for_n_days,
            }

        return variables.map_unique_id_to_long_term_high_low

    # Method to get highst and lowest price for intraday
    def get_intraday_highlow_values(self, duration_size="1 D", bar_size="1 min"):

        # Map of [conid][action] = req_id
        map_conid_action_to_req_id = {}

        # List of all request ids
        req_id_list = []

        # Create a local copy of 'cas_map_con_id_to_action_type_and_combo_type'
        cas_coinds_for_fetching_historical_data = copy.deepcopy(
            variables.cas_map_con_id_to_action_type_and_combo_type
        )

        for conid, sub_info_dict in cas_coinds_for_fetching_historical_data.items():
            contract = variables.map_con_id_to_contract[conid]

            # Create dict with conid as key
            if conid not in map_conid_action_to_req_id:
                map_conid_action_to_req_id[conid] = {}

            for action, sub_values in sub_info_dict.items():

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

        counter = 0
        while variables.cas_wait_time_for_historical_data > (
            counter * variables.sleep_time_waiting_for_tws_response
        ):

            # dict_mkt_end = variables.req_mkt_data_end
            # dicterr_msg = variables.req_error
            #
            # merged_dict = {}
            #
            # for key in set(dict_mkt_end.keys()) | set(dicterr_msg.keys()):
            #     if key in dict_mkt_end and key in dicterr_msg:
            #         merged_dict[key] = dict_mkt_end[key] or dicterr_msg[key]
            #     elif key in dict_mkt_end:
            #         merged_dict[key] = dict_mkt_end[key]
            #     else:
            #         merged_dict[key] = dicterr_msg[key]
            #
            # # If reqHistorical Data ended for all the reqId
            # if all([merged_dict[req_id] for req_id in req_id_list]):
            #     break

            # KARAN CHANGED IT - TODO - 20231027
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

    # Method to get current day open, highest and lowest price
    def get_current_day_open_highest_lowest_price(
        self, local_unique_id_to_combo_obj, map_conid_action_to_req_id
    ):

        # Dict
        local_map_unique_id_to_intraday_high_low = {}

        # Local copy of live price
        local_unique_id_to_prices_dict = copy.deepcopy(
            variables.unique_id_to_prices_dict
        )

        get_leg_div_by_combination_values_for_unique_id = {}

        for unique_id, combo_obj in local_unique_id_to_combo_obj.items():

            local_map_unique_id_to_intraday_high_low[unique_id] = {
                "1-Day Open": "N/A",
                "1-Day High": "N/A",
                "1-Day Low": "N/A",
                "Lowest Value TimeStamp": "N/A",
                "Highest Value TimeStamp": "N/A",
                "Intraday Resistance": "N/A",
                "Intraday Support": "N/A",
                "Intraday Resistance Count": "N/A",
                "Intraday Support Count": "N/A",
                "Current Day Open Price For Legs": "N/A",
                "Highest Price Comparison": "N/A",
                "Lowest Price Comparison": "N/A",
                "Intraday Price Range Ratio": "N/A",
                "Current Day Highest Price For Legs": "N/A",
                "Current Day Lowest Price For Legs": "N/A",
                "Current Day Current Candle For Legs": "N/A",
                "Day Open Or Current Candle": "N/A",
                "Price Support Ratio": "N/A",
                "Price Resistance Ratio": "N/A",
            }

            # TODO check here - Karan
            # Initialize dictionary for unique-id
            get_leg_div_by_combination_values_for_unique_id[unique_id] = {}

            get_leg_div_by_combination_values_for_unique_id[unique_id]["Leg 1"] = {
                "HV": "N/A",
                "Highest Value of Leg": "N/A",
                "Change in Price of Leg": "N/A",
            }

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
            if variables.flag_store_cas_tab_csv_files:

                for i, df_intraday_legwise in enumerate(all_data_frames):

                    file_path = rf"{variables.cas_tab_csv_file_path}\IntraDay\LegWise"
                    file_path += rf"\Unique_id_{unique_id}"

                    if not os.path.exists(file_path):
                        os.makedirs(file_path)

                    df_intraday_legwise.to_csv(
                        rf"{file_path}\Leg_{i+1}_Intraday.csv", index=False
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

            # Change from open %
            if is_data_frame_empty:
                local_map_unique_id_to_intraday_high_low[unique_id] = {
                    "1-Day Open": "N/A",
                    "1-Day High": "N/A",
                    "1-Day Low": "N/A",
                    "Lowest Value TimeStamp": "N/A",
                    "Highest Value TimeStamp": "N/A",
                    "Intraday Resistance": "N/A",
                    "Intraday Support": "N/A",
                    "Intraday Resistance Count": "N/A",
                    "Intraday Support Count": "N/A",
                    "Current Day Open Price For Legs": "N/A",
                    "Highest Price Comparison": "N/A",
                    "Lowest Price Comparison": "N/A",
                    "Intraday Price Range Ratio": "N/A",
                    "Current Day Highest Price For Legs": "N/A",
                    "Current Day Lowest Price For Legs": "N/A",
                    "Current Day Current Candle For Legs": "N/A",
                    "Day Open Or Current Candle": "N/A",
                    "Price Support Ratio": "N/A",
                    "Price Resistance Ratio": "N/A",
                }

                # TODO KARAN
                get_leg_div_by_combination_values_for_unique_id[unique_id]["Leg 1"] = {
                    "HV": "N/A",
                    "Highest Value of Leg": "N/A",
                    "Change in Price of Leg": "N/A",
                }
                continue

            # Merging the data frame, inner join on time
            merged_df = self.merge_dataframe_inner_join_with_combo_price_calculation(
                combo_obj, all_data_frames
            )

            # Calculate HV of leg divided by hv of combination for each leg
            hv_of_leg_since_open_div_by_hv_of_combination_since_open_value = (
                hv_of_leg_since_open_div_by_hv_of_combination_since_open(
                    unique_id, combo_obj, merged_df
                )
            )

            # Calculate Highest price of leg divided by Highest price of combination for each leg
            highest_price_of_leg_div_by_highest_price_of_combination_value = (
                highest_price_of_leg_div_by_highest_price_of_combination(
                    unique_id, combo_obj, merged_df
                )
            )

            # Calculate Change in price of leg divided by Change in price of combination for each leg
            change_in_price_for_leg_div_by_change_in_price_for_combination_value = (
                change_in_price_for_leg_div_by_change_in_price_for_combination(
                    unique_id, combo_obj, merged_df
                )
            )

            # Defining leg number to start with
            leg_number = 1

            # Iterate all 3 dictionaries
            for key1, key2, key3 in zip(
                hv_of_leg_since_open_div_by_hv_of_combination_since_open_value,
                highest_price_of_leg_div_by_highest_price_of_combination_value,
                change_in_price_for_leg_div_by_change_in_price_for_combination_value,
            ):

                get_leg_div_by_combination_values_for_unique_id[unique_id][
                    f"Leg {leg_number}"
                ] = {}
                # Store values of leg into dictionary
                get_leg_div_by_combination_values_for_unique_id[unique_id][
                    f"Leg {leg_number}"
                ][
                    f"HV for leg to Combo Comparison"
                ] = hv_of_leg_since_open_div_by_hv_of_combination_since_open_value[
                    key1
                ]
                get_leg_div_by_combination_values_for_unique_id[unique_id][
                    f"Leg {leg_number}"
                ][
                    f"Highest price for leg to Combo Comparison"
                ] = highest_price_of_leg_div_by_highest_price_of_combination_value[
                    key2
                ]
                get_leg_div_by_combination_values_for_unique_id[unique_id][
                    f"Leg {leg_number}"
                ][
                    f"Change in Price for leg to Combo Comparison"
                ] = change_in_price_for_leg_div_by_change_in_price_for_combination_value[
                    key3
                ]

                leg_number += 1

            variables.map_unique_id_to_leg_combo_comparision_val[
                unique_id
            ] = get_leg_div_by_combination_values_for_unique_id[unique_id]

            # Save DF to CSV File
            if variables.flag_store_cas_tab_csv_files:

                # Saving dataframe to csv
                file_path = rf"{variables.cas_tab_csv_file_path}\IntraDay\Merged"

                if not os.path.exists(file_path):
                    os.makedirs(file_path)

                merged_df.to_csv(
                    rf"{file_path}\Unique_Id_{unique_id}_IntraDay_all_legs_merged.csv",
                    index=False,
                )

            # Create new DataFrame with desired columns
            combination_price_dataframe = merged_df[
                ["Time", "Combination Open", "Combination Close"]
            ].copy()

            if variables.flag_weighted_change_in_price:

                # Get day open prices for each leg
                current_day_open_for_legs_list = get_values_for_each_leg(
                    merged_df, combo_obj
                )

                # Check flag indicating which candles to use either since start of day or current candle
                if not variables.flag_since_start_of_day_candles_for_relative_fields:
                    # Get day open or current candle values
                    values_to_calculate_change_from_open_value = (
                        get_values_for_each_leg(
                            merged_df,
                            combo_obj,
                            combo_price_type_highest_or_lowest_or_current="Current",
                        )
                    )

                else:

                    values_to_calculate_change_from_open_value = (
                        current_day_open_for_legs_list
                    )
            else:
                current_day_open_for_legs_list = "N/A"

            # Support resisatance, counts
            list_of_intraday_candles = [
                combination_price_dataframe["Combination Open"].tolist(),
                combination_price_dataframe["Combination Close"].tolist(),
            ]
            (
                significant_level_for_intraday,
                significant_level_count_values_for_intraday,
            ) = calc_signficant_levels(
                list_of_intraday_candles,
            )

            if unique_id > 0:

                (
                    significant_level_for_intraday_in_range,
                    significant_level_count_values_for_intraday_in_range,
                ) = calc_signficant_levels(
                    list_of_intraday_candles, flag_in_range=True, unique_id=unique_id
                )

            else:

                (
                    significant_level_for_intraday_in_range,
                    significant_level_count_values_for_intraday_in_range,
                ) = calc_signficant_levels(
                    list_of_intraday_candles, flag_in_range=True, unique_id=unique_id, combo_obj=combo_obj
                )



            # Defining resistance and support variables
            resistance, support = "N/A", "N/A"

            # Defining resistance count and support count variables
            resistane_count, support_count = "N/A", "N/A"

            try:
                resistane, support = "N/A", "N/A"

                if unique_id in local_unique_id_to_prices_dict:
                    # print("Here 1")
                    current_buy_price, current_sell_price = (
                        local_unique_id_to_prices_dict[unique_id]["BUY"],
                        local_unique_id_to_prices_dict[unique_id]["SELL"],
                    )

                    # print(current_buy_price, current_sell_price, "Prince")
                    # Calculating the Resistance, Support
                    (
                        resistance,
                        support,
                    ) = get_support_and_resitance_from_significant_levels(
                        significant_level_for_intraday,
                        current_buy_price,
                        current_sell_price,
                    )
                    # print(resistance, support, "Prince")

                    # Calculating the Resistance count, Support count
                    if resistance not in ["N/A", None, "None"]:
                        resistane_count = significant_level_count_values_for_intraday[
                            resistance
                        ]

                    if support not in ["N/A", None, "None"]:
                        support_count = significant_level_count_values_for_intraday[
                            support
                        ]

                    # print(resistane_count, support_count, "Count")
                else:
                    if unique_id > 0:
                        current_buy_price, current_sell_price = 'N/A', 'N/A'

                    for leg_obj in all_legs:
                        req_id = variables.con_id_to_req_id_dict[leg_obj.con_id]
                        bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]
                        current_buy_price, current_sell_price = ask, bid

                    # Calculating the Resistance, Support
                    (
                        resistance,
                        support,
                    ) = get_support_and_resitance_from_significant_levels(
                        significant_level_for_intraday,
                        current_buy_price,
                        current_sell_price,
                    )
                    # print(resistance, support, "Prince")

                    # Calculating the Resistance count, Support count
                    if resistance not in ["N/A", None, "None"]:
                        resistane_count = significant_level_count_values_for_intraday[
                            resistance
                        ]

                    if support not in ["N/A", None, "None"]:
                        support_count = significant_level_count_values_for_intraday[
                            support
                        ]


            except Exception as e:
                if variables.flag_debug_mode:
                    print(
                        f"Exception Occured For calculating intraday resistance and support, error is {e}"
                    )

            try:

                resistance_in_range, support_in_range = "N/A", "N/A"

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
                        significant_level_for_intraday_in_range,
                        current_buy_price,
                        current_sell_price,
                    )

                    # Make it available in variables
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
                    """'if resistance_in_range not in ["N/A", None, "None"]:
                        resistance_count_in_range = significant_level_count_values_for_intraday_in_range[
                            resistance_in_range]
                    else:
                        resistance_count_in_range = 'N/A'

                    if support_in_range not in ["N/A", None, "None"]:
                        support_count_in_range = significant_level_count_values_for_intraday_in_range[support_in_range]
                    else:
                        support_count_in_range = 'N/A""" ""

                else:

                    if unique_id > 0:
                        current_buy_price, current_sell_price = 'N/A', 'N/A'

                    for leg_obj in all_legs:
                        req_id = variables.con_id_to_req_id_dict[leg_obj.con_id]
                        bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]
                        current_buy_price, current_sell_price = ask, bid

                    # Calculating the Resistance, Support
                    (
                        resistance_in_range,
                        support_in_range,
                    ) = get_support_and_resitance_from_significant_levels(
                        significant_level_for_intraday_in_range,
                        current_buy_price,
                        current_sell_price,
                    )

                    # Make it available in variables
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
                resistance_in_range, support_in_range = "N/A", "N/A"
                resistance_count_in_range, support_count_in_range = "N/A", "N/A"
                if variables.flag_debug_mode:
                    print(
                        f"Exception Occured For calculating intraday resistance and support in range, error is {e}"
                    )

            # Column 4 - display the time at which highest and lowest price of the combination for the day were recorded.
            (
                lowest_value_timestamp,
                highest_value_timestamp,
            ) = get_timestamp_of_lowest_and_highest_point_of_price(
                combination_price_dataframe
            )

            high = None
            low = None
            day_open = None

            # Getting Min, Max value from the DataFrame
            for i, row in combination_price_dataframe.iterrows():

                # Open and Close Price of
                open_price = row["Combination Open"]
                close_price = row["Combination Close"]

                # Days Open
                if day_open == None:
                    day_open = close_price

                # Combination High
                if high == None or close_price > high:
                    high = close_price

                # Combination Low
                if low == None or close_price < low:
                    low = close_price

            # Format value 2 decimal
            high = "N/A" if high == None else int(high * 100) / 100
            low = "N/A" if low == None else int(low * 100) / 100
            day_open = "N/A" if day_open == None else int(day_open * 100) / 100

            # Check flag indicating which candles to use either since start of day or current candle
            if not variables.flag_since_start_of_day_candles_for_relative_fields:

                # Get day open or current candle values
                day_open_or_current_candle_price = (
                    current_candle
                ) = combination_price_dataframe["Combination Close"].iloc[-1]

            else:

                day_open_or_current_candle_price = day_open

            # Get comparison of prices in 2 time slots - Code
            # Initialize comparison of price variables for highest and lowest prices
            highest_price_comparison_intraday = "N/A"
            lowest_price_comparison_intraday = "N/A"

            try:
                # Divide combination df into 2 parts based on time frames
                [
                    recent_time_dataframe,
                    rest_of_day_dataframe,
                ] = self.divide_dataframe_based_on_two_time_frames(
                    combination_price_dataframe,
                    variables.time_frame_for_price_comparison_in_intraday,
                )

                # If dataframe for sub time frame in intraday s not N/A
                if not recent_time_dataframe.empty:

                    # Get highest price for recent time
                    recent_time_highest_price = recent_time_dataframe[
                        "Combination Close"
                    ].max()

                    # Get highest price for rest of day
                    rest_of_day_highest_price = rest_of_day_dataframe[
                        "Combination Close"
                    ].max()

                    # Get comparison of highest values in two time frames
                    highest_price_comparison_intraday = (
                        recent_time_highest_price > rest_of_day_highest_price
                    )

                    # Get lowest price for recent time
                    recent_time_lowest_price = recent_time_dataframe[
                        "Combination Close"
                    ].min()

                    # Get lowest price for rest of day
                    rest_of_day_lowest_price = rest_of_day_dataframe[
                        "Combination Close"
                    ].min()

                    # Get comparison of lowest values in two time frames
                    lowest_price_comparison_intraday = (
                        recent_time_lowest_price > rest_of_day_lowest_price
                    )

            except Exception as e:

                # Print to console
                if variables.flag_debug_mode:

                    print(
                        f"Exception inside calculating highest and lowest prices comparison, Exp: {e}"
                    )

            # Initialize price range inintraday
            intraday_price_range_ratio = "N/A"

            try:
                # Get dataframe for last hour
                [
                    prices_in_time_frame_dataframe,
                    _,
                ] = self.divide_dataframe_based_on_two_time_frames(
                    combination_price_dataframe,
                    variables.time_frame_for_price_range_ratio_in_intraday,
                )

                # Get highest for last hour
                highest_price_for_last_hour = prices_in_time_frame_dataframe[
                    "Combination Close"
                ].max()

                # # Get lowest price for last hour
                lowest_price_for_last_hour = prices_in_time_frame_dataframe[
                    "Combination Close"
                ].min()

                # Get price range for last hour
                price_range_in_time_frame = (
                    highest_price_for_last_hour - lowest_price_for_last_hour
                )

                # Calculate Combination Price Range for the last given time frame / Combination Price Range since the start of the day
                intraday_price_range_ratio = price_range_in_time_frame / (high - low)

            except Exception as e:

                # Print to console
                if variables.flag_debug_mode:

                    print(
                        f"Exception inside calculating intraday price range ratio comparison, Exp: {e}"
                    )

            # Get same combo highest price for each leg
            price_at_highest_combo_price_time_for_legs_list = (
                "N/A"
                if high == "N/A"
                else get_values_for_each_leg(
                    merged_df,
                    combo_obj,
                    combo_price_type_highest_or_lowest_or_current="Highest",
                )
            )

            # Get same combo lowest price for each leg
            price_at_lowest_combo_price_time_for_legs_list = (
                "N/A"
                if low == "N/A"
                else get_values_for_each_leg(
                    merged_df,
                    combo_obj,
                    combo_price_type_highest_or_lowest_or_current="Lowest",
                )
            )

            local_map_unique_id_to_intraday_high_low[unique_id] = {
                "1-Day Open": day_open,
                "1-Day High": high,
                "1-Day Low": low,
                "Lowest Value TimeStamp": lowest_value_timestamp,
                "Highest Value TimeStamp": highest_value_timestamp,
                "Intraday Resistance": resistance,
                "Intraday Support": support,
                "Intraday Resistance Count": resistane_count,
                "Intraday Support Count": support_count,
                "Current Day Open Price For Legs": current_day_open_for_legs_list,
                "Highest Price Comparison": highest_price_comparison_intraday,
                "Lowest Price Comparison": lowest_price_comparison_intraday,
                "Intraday Price Range Ratio": intraday_price_range_ratio,
                "Current Day Highest Price For Legs": price_at_highest_combo_price_time_for_legs_list,
                "Current Day Lowest Price For Legs": price_at_lowest_combo_price_time_for_legs_list,
                "Current Day Current Candle For Legs": values_to_calculate_change_from_open_value,
                "Day Open Or Current Candle": day_open_or_current_candle_price,
                "Price Support Ratio": support_in_range,
                "Price Resistance Ratio": resistance_in_range,
            }

            try:

                variables.map_unique_id_to_intraday_high_low[
                    unique_id
                ] = local_map_unique_id_to_intraday_high_low[unique_id]

            except Exception as e:

                if variables.flag_debug_mode:

                    print(f"Exception insode assigning intraday values: Exp: {e}")

        # Setting updated value in the variables dict
        # variables.map_unique_id_to_intraday_high_low = local_map_unique_id_to_intraday_high_low

        return local_map_unique_id_to_intraday_high_low

    # Method to divide dataframe in 2 parts based on time frame
    def divide_dataframe_based_on_two_time_frames(
        self, combination_dataframe, sub_time_frame_in_intraday
    ):

        try:
            # Get number of rows in dataframe
            length_of_dataframe = len(combination_dataframe)

            # time frame in intraday combo dataframe must be bigger than sub time frame in intraday
            if length_of_dataframe <= sub_time_frame_in_intraday:

                return [pd.DataFrame(), pd.DataFrame()]

            # Get the last 10 rows of the DataFrame and store it in another variable
            recent_time_dataframe = combination_dataframe.tail(
                sub_time_frame_in_intraday
            )

            # Create a new dataframe with all rows except the last 10
            rest_of_day_dataframe = combination_dataframe.iloc[
                : -1 * sub_time_frame_in_intraday
            ]

            return [recent_time_dataframe, rest_of_day_dataframe]
        except Exception as e:

            return [pd.DataFrame(), pd.DataFrame()]

    # Method to manage intraday values calculations
    def update_intraday_values(self, conid_list=None, unique_id_added=None):

        # local copy of 'unique_id_to_combo_obj'
        local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

        # Init
        duration_size = "1 D"
        bar_size = "1 min"

        # Requesting historical data and getting reqid
        map_conid_action_bar_size_to_req_id = self.get_intraday_highlow_values(
            duration_size, bar_size
        )

        if conid_list != None:

            # Create a filtered dictionary using a dictionary comprehension
            cas_coinds_for_fetching_historical_data = {
                key: map_conid_action_bar_size_to_req_id[key] for key in conid_list
            }

            # local copy of 'unique_id_to_combo_obj'
            local_unique_id_to_combo_obj = {
                unique_id_added: local_unique_id_to_combo_obj[unique_id_added]
            }

            local_cas_unique_id_to_combo_obj = {}

        max_id = 0

        local_unique_id_to_combo_obj_loop_copy = copy.deepcopy(local_unique_id_to_combo_obj)

        # Add combo object for legs separately to calculate legs indicator values
        for unique_id_combo in local_unique_id_to_combo_obj_loop_copy:

            variables.map_unique_id_to_legs_unique_id[unique_id_combo] = {'Leg Unique Ids': [], 'Combo Obj List': []}

            combo_obj = local_unique_id_to_combo_obj[unique_id_combo]

            all_legs = combo_obj.buy_legs + combo_obj.sell_legs

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

                variables.map_unique_id_to_legs_unique_id[unique_id_combo]['Leg Unique Ids'].append(max_id * -1)

                variables.map_unique_id_to_legs_unique_id[unique_id_combo]['Combo Obj List'].append(combination_obj)

                local_unique_id_to_combo_obj[max_id * -1] = combination_obj

        # Getting Highest and Lowest Price of combo for current day
        map_unique_id_to_high_low = self.get_current_day_open_highest_lowest_price(
            local_unique_id_to_combo_obj, map_conid_action_bar_size_to_req_id
        )

        # Print to console
        if variables.flag_debug_mode:
            print(f"\nIntra-Day")

        # Updating IntraDay Values in DB
        for unique_id_, values in map_unique_id_to_high_low.items():
            # Print to console
            if variables.flag_debug_mode:
                print(unique_id_, values)

            day_open = values["1-Day Open"]
            day_high = values["1-Day High"]
            day_low = values["1-Day Low"]

            # update the new calculated values in DB
            # update_high_low_price_in_db(unique_id_, day_high, day_low, is_intraday= True)

        # Update the last updated time of intraday values
        update_last_longterm_or_intraday_updated_time(is_intraday=True)

    # Method to calculate ATR and last close price
    def calculate_combo_atr_and_last_close_price(
        self, unique_id, combo_open_close_df, flag_order_paramrameter_atr=False
    ):

        if not flag_order_paramrameter_atr:
            # Group dataframe by date and get 1d candle (first open, last close)
            combo_daily_open_close_df = (
                self.group_dataframe_by_time_and_create_1d_candle_first_open_last_close(
                    combo_open_close_df
                )
            )
        else:
            combo_daily_open_close_df = combo_open_close_df.copy()

        # Save DF to CSV File
        if variables.flag_store_cas_tab_csv_files and not flag_order_paramrameter_atr:

            # Saving dataframe to csv
            file_path = rf"{variables.cas_tab_csv_file_path}\ATR"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            combo_daily_open_close_df.to_csv(
                rf"{file_path}\Unique_Id_{unique_id}_Combined.csv", index=False
            )

        elif variables.flag_store_cas_tab_csv_files and flag_order_paramrameter_atr:

            # Saving dataframe to csv
            file_path = rf"{variables.cas_tab_csv_file_path}\Order Parameter ATR\ATR"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            combo_daily_open_close_df.to_csv(
                rf"{file_path}\Unique_Id_{unique_id}_Combined.csv", index=False
            )

        # Take 'K' Data Points
        k = variables.atr_number_of_days

        # Take Latest 'k' daily candle
        if len(combo_daily_open_close_df) > variables.atr_number_of_days:
            combo_daily_open_close_df = combo_daily_open_close_df.tail(k).reset_index(
                drop=True
            )

        # Calculate TR
        combo_daily_open_close_df["TR"] = 0.0
        for i in range(len(combo_daily_open_close_df)):
            if i == 0:
                combo_daily_open_close_df.loc[i, "TR"] = max(
                    combo_daily_open_close_df.loc[i, "Combination Open"],
                    combo_daily_open_close_df.loc[i, "Combination Close"],
                ) - min(
                    combo_daily_open_close_df.loc[i, "Combination Open"],
                    combo_daily_open_close_df.loc[i, "Combination Close"],
                )
            else:
                combo_daily_open_close_df.loc[i, "TR"] = max(
                    combo_daily_open_close_df.loc[i, "Combination Open"],
                    combo_daily_open_close_df.loc[i, "Combination Close"],
                    combo_daily_open_close_df.loc[i - 1, "Combination Close"],
                ) - min(
                    combo_daily_open_close_df.loc[i, "Combination Open"],
                    combo_daily_open_close_df.loc[i, "Combination Close"],
                    combo_daily_open_close_df.loc[i - 1, "Combination Close"],
                )

        # Calculate ATR
        combo_daily_open_close_df["ATR"] = 0.0
        for i in range(len(combo_daily_open_close_df)):
            if i == 0:
                combo_daily_open_close_df.loc[i, "ATR"] = combo_daily_open_close_df.loc[
                    i, "TR"
                ]
            else:
                combo_daily_open_close_df.loc[i, "ATR"] = (
                    combo_daily_open_close_df.loc[i - 1, "ATR"] * (k - 1)
                    + combo_daily_open_close_df.loc[i, "TR"]
                ) / k

        # Save DF to CSV File
        if variables.flag_store_cas_tab_csv_files and not flag_order_paramrameter_atr:

            # Saving dataframe to csv
            file_path = rf"{variables.cas_tab_csv_file_path}\ATR"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            combo_daily_open_close_df.to_csv(
                rf"{file_path}\Unique_Id_{unique_id}_ATR.csv", index=False
            )

        elif variables.flag_store_cas_tab_csv_files and flag_order_paramrameter_atr:

            # Saving dataframe to csv
            file_path = rf"{variables.cas_tab_csv_file_path}\Order Parameter ATR\ATR"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            combo_daily_open_close_df.to_csv(
                rf"{file_path}\Unique_Id_{unique_id}_ATR.csv", index=False
            )

        # ATR
        try:
            atr = combo_daily_open_close_df.iloc[-1]["ATR"]
        except Exception as e:
            # Print to console
            if variables.flag_debug_mode:
                print("Unable to calculate ATR")
            atr = None

        # Last Close
        try:
            # current_date_time = datetime.datetime.now(variables.target_timezone_obj)
            # yesterday_date = current_date_time - datetime.timedelta(days=1)
            # formatted_yesterdays_date = yesterday_date.strftime("%Y-%m-%d")
            # pd_yesterday_date = pd.to_datetime(formatted_yesterdays_date)

            # Confirm This
            close_price = combo_daily_open_close_df.iloc[-2]["Combination Close"]

        except Exception as e:
            # Print to console
            if variables.flag_debug_mode:
                print("Unable to get Combo close")
            close_price = None

        return atr, close_price

    # Method to merge dataframe to get price dataframe for combo
    def merge_dataframe_inner_join_with_combo_price_calculation(
        self, combo_obj, all_data_frames
    ):

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
            quantity = int(leg_obj.quantity)
            multiplier = leg_obj.multiplier

            if (multiplier == None) or (multiplier == "None"):
                multiplier = 1
            else:
                multiplier = int(multiplier)

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

    # Used when calculating ATR and Correlation
    def group_dataframe_by_time_and_create_1d_candle_first_open_last_close(
        self, combo_open_close_df
    ):
        # 'combo_open_close_df' will have Combination Open and Combination Close

        try:
            combo_open_close_df["Time"] = pd.to_datetime(combo_open_close_df["Time"])

            # group the data by date
            combo_open_close_df = combo_open_close_df.groupby(
                combo_open_close_df["Time"].dt.date
            )

            # define the aggregation functions
            agg_funcs = {"first", "last"}

            # apply the aggregation functions to each group
            combo_daily_open_close_df = combo_open_close_df["Combination Close"].agg(
                agg_funcs
            )

            # Converting multi-level columns to single-level columns
            combo_daily_open_close_df.columns = combo_daily_open_close_df.columns.map(
                "".join
            )

            # Resetting index of dataframe
            combo_daily_open_close_df = combo_daily_open_close_df.reset_index()

            # Renaming columns from 'first' to  'Combination Open' and from 'last' to  'Combination close'
            combo_daily_open_close_df = combo_daily_open_close_df.rename(
                columns={
                    "Time": "Date",
                    "first": "Combination Open",
                    "last": "Combination Close",
                }
            )

        except Exception as e:
            print(f"Exception while making daily candles from 1hr candle: {e}")

            # Returning Empty Data frame
            return pd.DataFrame()

        # Print to console
        if variables.flag_debug_mode:
            print(
                "\nGroup_dataframe_by_time_and_create_1d_candle_first_open_last_close"
            )
            print(combo_daily_open_close_df)

        return combo_daily_open_close_df

    # Method to calculate correlation
    def calculate_correlation_for_cas_unique_ids(
        self,
        unique_id,
        active_combo_legs_dataframe,
        cas_legs_dataframe,
    ):

        # Pass
        combo_daily_open_close_df = (
            self.group_dataframe_by_time_and_create_1d_candle_first_open_last_close(
                active_combo_legs_dataframe
            )
        )

        # drop the 'Combination Open' column
        combo_daily_open_close_df = combo_daily_open_close_df.drop(
            "Combination Open", axis=1
        )

        cas_combo_daily_open_close_df = (
            self.group_dataframe_by_time_and_create_1d_candle_first_open_last_close(
                cas_legs_dataframe
            )
        )

        # drop the 'Combination Open' column
        cas_combo_daily_open_close_df = cas_combo_daily_open_close_df.drop(
            "Combination Open", axis=1
        )

        # rename to 'Combination Close' to 'CAS Close'
        cas_combo_daily_open_close_df.columns = ["Date", "CAS Close"]

        # Save DF to CSV File
        if variables.flag_store_cas_tab_csv_files:

            # Saving dataframe to csv
            file_path = rf"{variables.cas_tab_csv_file_path}\Correlation"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            combo_daily_open_close_df.to_csv(
                rf"{file_path}\Unique_Id_{unique_id}_Existing_combo_combined.csv",
                index=False,
            )
            cas_combo_daily_open_close_df.to_csv(
                rf"{file_path}\Unique_Id_{unique_id}_Incremental_combo_combined.csv",
                index=False,
            )

        merged_df_with_close = pd.merge(
            combo_daily_open_close_df,
            cas_combo_daily_open_close_df,
            on="Date",
            how="inner",
        )

        # Dropping nan values, if any
        merged_df_with_close = merged_df_with_close.dropna()

        # Save DF to CSV File
        if variables.flag_store_cas_tab_csv_files:

            # Saving dataframe to csv
            file_path = rf"{variables.cas_tab_csv_file_path}\Correlation"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            merged_df_with_close.to_csv(
                rf"{file_path}\Unique_Id_{unique_id}_Existing_Incremental_combo_combined.csv",
                index=False,
            )

        # Convert dataframe into series
        list1 = merged_df_with_close["Combination Close"]
        list2 = merged_df_with_close["CAS Close"]

        # if len of lists are 0, return None
        if len(list1) < 1:
            return None

        # Apply the pearsonr()
        corr, _ = pearsonr(list1, list2)

        return corr

    # Get dataframe of historical data for combo
    def get_the_dataframe_that_contains_historical_data_for_combo(
        self, combo_obj, map_conid_action_bar_size_to_req_id, df_for_hv=False
    ):

        # All Legs in combo
        buy_legs = combo_obj.buy_legs
        sell_legs = combo_obj.sell_legs
        all_legs = buy_legs + sell_legs

        # what data do we need for the combo 1Day or 1H for CAS(N-Day) Longterm Values
        only_stk_fut = False

        # Checking Combo type, and map con_id to contract
        for leg_obj_ in buy_legs + sell_legs:

            if leg_obj_.sec_type in ["OPT", "FOP"]:
                only_stk_fut = False

        # bar size for the unique id combo,
        bar_size = "1D" if only_stk_fut else "1H"

        # list of request_id
        req_id_list = []

        # Get all reqId (reqHisData) so we can get dataframe,
        for leg in all_legs:

            # Action and con_id of leg
            action = leg.action
            con_id = leg.con_id

            try:
                # reqId that contains historicaldata
                if df_for_hv == True:
                    req_id = map_conid_action_bar_size_to_req_id[con_id][action]
                else:
                    req_id = map_conid_action_bar_size_to_req_id[con_id][action][bar_size]
            except Exception as exp:
                # TODO - Remoe this later on
                # print("Inside HighLowCal Line 1726", exp)
                # print(f"Conid: {con_id} Action: {action} BarSize: {bar_size}")
                # print(f"{map_conid_action_bar_size_to_req_id=}")

                req_id = -1

                # Map req_id to dataframe containing historical_data
                variables.map_req_id_to_historical_data_dataframe[-1] = pd.DataFrame(
                    columns=variables.historical_data_columns
                )

            req_id_list.append(req_id)

        # All Data Frames,
        all_data_frames = [
            variables.map_req_id_to_historical_data_dataframe[req_id]
            for req_id in req_id_list
        ]

        return all_data_frames

    # Method to calculate average of absolute change in price for lookback period
    def calculate_avg_of_abs_change_in_price_for_the_same_time_period(
        self,
        unique_id,
        lookback_period_dataframe,
        date_time_start,
        date_time_close,
    ):

        # Get combo obj
        try:
            local_unique_id_to_combo_obj = copy.deepcopy(
                variables.unique_id_to_combo_obj
            )
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
            if variables.flag_store_cas_tab_csv_files:

                file_path = rf"{variables.cas_tab_csv_file_path}\Price\RelativeChange"

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
            day_start_values_for_day_row = (
                date_specific_dataframe_for_change_in_price.head(1)
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

            if calculated_change_in_for_look_back_days == []:

                avg_of_change_in_prices_over_lookback = "N/A"
            else:

                avg_of_change_in_prices_over_lookback = np.mean(
                    calculated_change_in_for_look_back_days
                )
        except Exception as e:
            print(
                f"Inside 'calculate_avg_of_abs_change_in_price_for_the_same_time_period', error is {e}"
            )
            avg_of_change_in_prices_over_lookback = "N/A"

        return avg_of_change_in_prices_over_lookback

    # Method to calculate beta value
    def calculate_beta_value(self, unique_id, index_data_frame, combination_data_frame):

        all_data_frames = [index_data_frame, combination_data_frame]

        merged_df = all_data_frames[0]

        # Merging all data frames such that Time is available in all data frames
        for i, df_ith in enumerate(all_data_frames[1:]):
            merged_df = pd.merge(
                merged_df, df_ith, on="Date", how="inner", suffixes=(f"", f" {i+1}")
            )

        # Dropping nan values, if any
        merged_df = merged_df.dropna()

        merged_df.columns = [
            "Date",
            "Index Open Price",
            "Index Close Price",
            "Combination Open",
            "Combination Close",
        ]

        if len(merged_df) < 2:

            # Return Beta value 'N/A'
            return "N/A"

        try:

            # Calculating the return for index
            merged_df["Return For Index"] = np.log(
                np.abs(merged_df["Index Close Price"]) + 1
            ) * np.sign(merged_df["Index Close Price"]) - np.log(
                np.abs(merged_df["Index Close Price"].shift(1)) + 1
            ) * np.sign(
                merged_df["Index Close Price"].shift(1)
            )

            # Calculating the return for combination
            merged_df["Return For Combination"] = np.log(
                np.abs(merged_df["Combination Close"]) + 1
            ) * np.sign(merged_df["Combination Close"]) - np.log(
                np.abs(merged_df["Combination Close"].shift(1)) + 1
            ) * np.sign(
                merged_df["Combination Close"].shift(1)
            )

            # Covariance b/t index and combination
            co_variance = merged_df["Return For Index"].cov(
                merged_df["Return For Combination"]
            )

            # Variance of Index
            variance = merged_df["Return For Index"].var()

        except Exception as e:
            # print(e)
            if variables.flag_debug_mode:
                print("Inside beta calculation", e)

        # Save DF to CSV File (HV) Export data-frame to csv file
        if variables.flag_store_cas_tab_csv_files:

            file_path = rf"{variables.cas_tab_csv_file_path}\Beta"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            # Saving CSV
            merged_df.to_csv(
                rf"{file_path}\beta calculation values for unique-id {unique_id}.csv",
                index=False,
            )

        try:

            co_variance = float(co_variance)
            variance = float(variance)

            if variance != 0:
                beta_value = co_variance / variance

            else:
                beta_value = "N/A"

            if math.isnan(beta_value):
                raise Exception("Error beta value is NaN")
        except Exception as e:
            beta_value = "N/A"

            if variables.flag_debug_mode:
                print(f"Inside 'calculate_beta_value' error is, {e}")

        return beta_value

    # Method to request historical data for index
    def historical_data_for_index(
        self, duration_size_for_index_data, bar_size_for_index_data
    ):

        # TODO KARAN ASHISH CRItiCAL tODO NEED TO CHeCK it
        # Getting req_id
        req_id = variables.app.nextorderId
        variables.app.nextorderId += 1

        # Request historical data
        request_historical_price_data_for_contract(
            variables.beta_contract,
            bar_size_for_index_data,
            duration_size_for_index_data,
            "BID",
            req_id=req_id,
            cas_app=False,
        )

        # Counter for wait
        counter = 0

        # Keep Waiting for data till  'cas_wait_time_for_historical_data' time
        while variables.cas_wait_time_for_historical_data > (
            counter * variables.sleep_time_waiting_for_tws_response
        ):

            # If reqHistorical Data ended for all the reqId or Got Error for any of the reqId
            if all([variables.req_mkt_data_end[req_id]]) or any(
                [variables.req_error[req_id]]
            ):
                break

            # Sleep for sleep_time_waiting_for_tws_response
            time.sleep(variables.sleep_time_waiting_for_tws_response)

            # Increase Counter
            counter += 1

        index_dataframe = variables.map_req_id_to_historical_data_dataframe[req_id]
        # NEW BETA file INDEX_PRICE
        # Unique ( save acc.)
        # SAVE THIS DATA FRAME

        # Save DF to CSV File (HV) Export data-frame to csv file
        if variables.flag_store_cas_tab_csv_files:

            file_path = rf"{variables.cas_tab_csv_file_path}\Beta"

            if not os.path.exists(file_path):
                os.makedirs(file_path)

            # Saving CSV
            index_dataframe.to_csv(
                rf"{file_path}\historical data for index {variables.index_select_for_beta_column}.csv",
                index=False,
            )

        return index_dataframe

    # Method to calculate last candle for order parameter
    def get_last_candle_for_order(self, conid_list=None, unique_id_added=None):

        # Init
        unique_id_to_candle_dict = {}

        try:

            # All active combos in the system
            local_unique_id_to_combo_obj = copy.deepcopy(
                variables.unique_id_to_combo_obj
            )

            # Info 'cas_coinds_for_fetching_historical_data' contains dict
            cas_coinds_for_fetching_historical_data = copy.deepcopy(
                variables.cas_map_con_id_to_action_type_and_combo_type
            )

            if conid_list != None:
                # Create a filtered dictionary using a dictionary comprehension
                cas_coinds_for_fetching_historical_data = {
                    key: cas_coinds_for_fetching_historical_data[key]
                    for key in conid_list
                }

                # local copy of 'unique_id_to_combo_obj'
                local_unique_id_to_combo_obj = {
                    unique_id_added: local_unique_id_to_combo_obj[unique_id_added]
                }

            #print(variables.order_parameter_candle_candle_size)

            # Requesting Historical data for all the combos, for ATR Calculation
            map_conid_action_to_req_id = self.get_historical_data_for_hv(
                cas_coinds_for_fetching_historical_data,
                2,
                variables.order_parameter_candle_candle_size,
            )

            # Want dataframe for candle Calculation
            df_for_candle = True

            # Getting the Combo Open and Close Dataframe for each combo,
            for unique_id, combo_obj in local_unique_id_to_combo_obj.items():

                try:

                    all_data_frames = (
                        self.get_the_dataframe_that_contains_historical_data_for_combo(
                            combo_obj, map_conid_action_to_req_id, df_for_candle
                        )
                    )

                    # Save DF to CSV File (HV)
                    if variables.flag_store_cas_tab_csv_files:

                        # Save all DF to CSV
                        for i, df_hv_legwise in enumerate(all_data_frames):

                            file_path = rf"{variables.cas_tab_csv_file_path}\Order Parameter Candle\LegWise\Unique_id_{unique_id}"

                            if not os.path.exists(file_path):
                                os.makedirs(file_path)

                            df_hv_legwise.to_csv(
                                rf"{file_path}\Leg_{i + 1}.csv", index=False
                            )

                    # Data not found for any leg
                    is_data_frame_empty = False

                    # If data is not present
                    for i, dataframe in enumerate(all_data_frames):
                        if (
                                dataframe is None
                                or len(dataframe.index) == 0
                                or dataframe.empty
                        ):
                            is_data_frame_empty = True

                            # Print to console
                            if variables.flag_debug_mode:
                                print(f"Empty Dataframe for Unique ID: {unique_id}")
                            break

                    # Merging the data frame, inner join on time
                    merged_df = (
                        self.merge_dataframe_inner_join_with_combo_price_calculation(
                            combo_obj, all_data_frames
                        )
                    )

                    # Save DF to CSV File
                    if variables.flag_store_cas_tab_csv_files:

                        # Saving dataframe to csv
                        file_path = rf"{variables.cas_tab_csv_file_path}\Order Parameter Candle\Merged"

                        if not os.path.exists(file_path):
                            os.makedirs(file_path)

                        merged_df.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_candle_all_legs_merged.csv",
                            index=False,
                        )

                    # Create new DataFrame with desired columns
                    combination_price_dataframe = merged_df[
                        ["Time", "Combination Open", "Combination Close"]
                    ].copy()

                    if combination_price_dataframe.empty:

                        continue







                    # Get the last row of the DataFrame
                    last_row = combination_price_dataframe.iloc[-2]

                    high_val = max(last_row["Combination Open"], last_row["Combination Close"])
                    low_val = min(last_row["Combination Open"], last_row["Combination Close"])

                    unique_id_to_candle_dict[unique_id] = {}

                    unique_id_to_candle_dict[unique_id]['High Candle Value'] = round(high_val, 4)
                    unique_id_to_candle_dict[unique_id]['Low Candle Value'] = round(low_val, 4)

                    # assign value to global dictionary
                    variables.map_unique_id_to_candle_for_order_values[
                        unique_id
                    ] = unique_id_to_candle_dict[unique_id]

                except Exception as e:

                    unique_id_to_candle_dict[unique_id] = {}

                    unique_id_to_candle_dict[unique_id]['High Candle Value'] = "N/A"
                    unique_id_to_candle_dict[unique_id]['Low Candle Value'] = "N/A"

                    # assign value to global dictionary
                    variables.map_unique_id_to_candle_for_order_values[
                        unique_id
                    ] = unique_id_to_candle_dict[unique_id]

        except Exception as e:

            # Print to console
            if variables.flag_debug_mode:
                print(f"Exception inside 'calculate_atr_for_order', Exp: {e}")

            return "N/A"

    # Method to calculate ATR as order parameter
    def calculate_atr_for_order(self, conid_list=None, unique_id_added=None):

        # Init
        unique_id_to_atr_dict = {}



        try:
            # Init
            calculated_atr = "N/A"

            # All active combos in the system
            local_unique_id_to_combo_obj = copy.deepcopy(
                variables.unique_id_to_combo_obj
            )

            # Info 'cas_coinds_for_fetching_historical_data' contains dict
            cas_coinds_for_fetching_historical_data = copy.deepcopy(
                variables.cas_map_con_id_to_action_type_and_combo_type
            )

            if conid_list != None:
                # Create a filtered dictionary using a dictionary comprehension
                cas_coinds_for_fetching_historical_data = {
                    key: cas_coinds_for_fetching_historical_data[key]
                    for key in conid_list
                }

                # local copy of 'unique_id_to_combo_obj'
                local_unique_id_to_combo_obj = {
                    unique_id_added: local_unique_id_to_combo_obj[unique_id_added]
                }

            # Requesting Historical data for all the combos, for ATR Calculation
            map_conid_action_to_req_id = self.get_historical_data_for_hv(
                cas_coinds_for_fetching_historical_data,
                variables.order_parameter_atr_lookback_days,
                variables.order_parameter_atr_candle_size,
            )

            # Want dataframe for HV Calculation
            df_for_hv = True

            # Getting the Combo Open and Close Dataframe for each combo,
            for unique_id, combo_obj in local_unique_id_to_combo_obj.items():

                try:

                    all_data_frames = (
                        self.get_the_dataframe_that_contains_historical_data_for_combo(
                            combo_obj, map_conid_action_to_req_id, df_for_hv
                        )
                    )

                    # Save DF to CSV File (HV)
                    if variables.flag_store_cas_tab_csv_files:

                        # Save all DF to CSV
                        for i, df_hv_legwise in enumerate(all_data_frames):

                            file_path = rf"{variables.cas_tab_csv_file_path}\Order Parameter ATR\LegWise\Unique_id_{unique_id}"

                            if not os.path.exists(file_path):
                                os.makedirs(file_path)

                            df_hv_legwise.to_csv(
                                rf"{file_path}\Leg_{i+1}.csv", index=False
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
                                print(f"Empty Dataframe for Unique ID: {unique_id}")
                            break

                    # Merging the data frame, inner join on time
                    merged_df = (
                        self.merge_dataframe_inner_join_with_combo_price_calculation(
                            combo_obj, all_data_frames
                        )
                    )

                    # Save DF to CSV File
                    if variables.flag_store_cas_tab_csv_files:

                        # Saving dataframe to csv
                        file_path = rf"{variables.cas_tab_csv_file_path}\Order Parameter ATR\Merged"

                        if not os.path.exists(file_path):
                            os.makedirs(file_path)

                        merged_df.to_csv(
                            rf"{file_path}\Unique_Id_{unique_id}_HV_all_legs_merged.csv",
                            index=False,
                        )

                    # Create new DataFrame with desired columns
                    combination_price_dataframe = merged_df[
                        ["Time", "Combination Open", "Combination Close"]
                    ].copy()

                    # Calculate the ATR for combination
                    calculated_atr, _ = self.calculate_combo_atr_and_last_close_price(
                        unique_id,
                        combination_price_dataframe,
                        flag_order_paramrameter_atr=True,
                    )

                    unique_id_to_atr_dict[unique_id] = round(calculated_atr, 4)

                    # assign value to global dictionary
                    variables.map_unique_id_to_atr_for_order_values[
                        unique_id
                    ] = unique_id_to_atr_dict[unique_id]

                except Exception as e:

                    unique_id_to_atr_dict[unique_id] = "N/A"

                    # assign value to global dictionary
                    variables.map_unique_id_to_atr_for_order_values[
                        unique_id
                    ] = unique_id_to_atr_dict[unique_id]

        except Exception as e:

            # Print to console
            if variables.flag_debug_mode:

                print(f"Exception inside 'calculate_atr_for_order', Exp: {e}")

            return "N/A"

    # Method to calculate HV values
    def calculate_hv_related_columns(self, conid_list=None, unique_id_added=None):

        # Calculate order parameter ATR
        # unique_id_to_order_parameter_atr_dict = self.calculate_atr_for_order()

        # All active combos in the system
        local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

        # Info 'cas_coinds_for_fetching_historical_data' contains dict {coind : {BUY : 1H 1D ,  SELL: 1H 1D} }
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

            local_cas_unique_id_to_combo_obj = {}

        max_id = 0

        local_unique_id_to_combo_obj_loop_copy = copy.deepcopy(local_unique_id_to_combo_obj)

        for unique_id_combo in local_unique_id_to_combo_obj_loop_copy:

            variables.map_unique_id_to_legs_unique_id[unique_id_combo] = {'Leg Unique Ids': [], 'Combo Obj List': []}

            combo_obj = local_unique_id_to_combo_obj[unique_id_combo]

            all_legs = combo_obj.buy_legs + combo_obj.sell_legs

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

                variables.map_unique_id_to_legs_unique_id[unique_id_combo]['Leg Unique Ids'].append(max_id * -1)

                variables.map_unique_id_to_legs_unique_id[unique_id_combo]['Combo Obj List'].append(combination_obj)

                local_unique_id_to_combo_obj[max_id * -1] = combination_obj

        # Requesting Historical data for all the combos, for HV Calculation
        map_conid_action_to_req_id = self.get_historical_data_for_hv(
            cas_coinds_for_fetching_historical_data,
            variables.hv_look_back_days,
            variables.hv_candle_size,
        )

        # Want dataframe for HV Calculation
        df_for_hv = True

        # Dict to store all the computed values
        hv_values = {}

        # Getting the Combo Open and Close Dataframe for each combo,
        for unique_id, combo_obj in local_unique_id_to_combo_obj.items():

            all_data_frames = (
                self.get_the_dataframe_that_contains_historical_data_for_combo(
                    combo_obj, map_conid_action_to_req_id, df_for_hv
                )
            )

            # Save DF to CSV File (HV)
            if variables.flag_store_cas_tab_csv_files:

                # Save all DF to CSV
                for i, df_hv_legwise in enumerate(all_data_frames):

                    file_path = rf"{variables.cas_tab_csv_file_path}\HV\LegWise\Unique_id_{unique_id}"

                    if not os.path.exists(file_path):
                        os.makedirs(file_path)

                    df_hv_legwise.to_csv(rf"{file_path}\Leg_{i+1}.csv", index=False)

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
                        print(f"Empty Dataframe for Unique ID: {unique_id}")
                    break

            # Set Values to N/A for Unique ID
            if is_data_frame_empty:
                hv_values[unique_id] = {
                    "H. V.": "N/A",
                    "H.V. Without Annualized": "N/A",
                    "Candle Volatility": "N/A",
                    "Order Parameter ATR": "N/A",
                }
                continue

            # Merging the data frame, inner join on time
            merged_df = self.merge_dataframe_inner_join_with_combo_price_calculation(
                combo_obj, all_data_frames
            )

            # Save DF to CSV File
            if variables.flag_store_cas_tab_csv_files:

                # Saving dataframe to csv
                file_path = rf"{variables.cas_tab_csv_file_path}\HV\Merged"

                if not os.path.exists(file_path):
                    os.makedirs(file_path)

                merged_df.to_csv(
                    rf"{file_path}\Unique_Id_{unique_id}_HV_all_legs_merged.csv",
                    index=False,
                )

            # Create new DataFrame with desired columns
            combination_price_dataframe = merged_df[
                ["Time", "Combination Open", "Combination Close"]
            ].copy()

            try:
                # Create a new dataframe having the latest day available vlaues, and reset index
                latest_available_date = combination_price_dataframe.iloc[-1][
                    "Time"
                ].date()
                latest_day_dataframe = combination_price_dataframe[
                    combination_price_dataframe["Time"].dt.date == latest_available_date
                ].copy()

                # Reset the index of dataframes
                latest_day_dataframe = latest_day_dataframe.reset_index(drop=True)

                # Number of Candles in Latest Day Dataframe
                number_of_candles_since_day_open = len(latest_day_dataframe)

                # Current Buy and sell price of combination
                current_price_and_spread_of_combo_dict = copy.deepcopy(
                    variables.unique_id_to_prices_dict
                )

                if unique_id in current_price_and_spread_of_combo_dict:

                    buy_price, sell_price = (
                        current_price_and_spread_of_combo_dict[unique_id]["BUY"],
                        current_price_and_spread_of_combo_dict[unique_id]["SELL"],
                    )

                    # Avg. Price of combo
                    avg_price_combo = (buy_price + sell_price) / 2

                elif unique_id < 0:

                    for leg_obj in all_legs:
                        req_id = variables.con_id_to_req_id_dict[leg_obj.con_id]
                        bid, ask = variables.bid_price[req_id], variables.ask_price[req_id]
                        # Avg. Price of combo
                        avg_price_combo = (ask + bid) / 2

                else:

                    avg_price_combo = 'N/A'

            except Exception as e:

                # Print to console:
                if variables.flag_debug_mode:
                    print(f"Could not compute the H. V. Related value. Exception {e}")

                hv_values[unique_id] = {
                    "H. V.": "N/A",
                    "H.V. Without Annualized": "N/A",
                    "Candle Volatility": "N/A",
                    "Order Parameter ATR": "N/A",
                }

                continue

            # Getting list of combination open prices and combination close prices for recent or current day
            current_day_open_prices = latest_day_dataframe["Combination Open"].tolist()
            current_day_close_prices = latest_day_dataframe[
                "Combination Close"
            ].tolist()

            # check if flag for calculating hv for daily candles is true
            if variables.flag_hv_daily:

                # Get dataframe with 1 D candles
                combination_price_dataframe_for_hv = self.group_dataframe_by_time_and_create_1d_candle_first_open_last_close(
                    combination_price_dataframe.copy()
                )

            # If flag for calculating hv for daily candles is false
            else:

                combination_price_dataframe_for_hv = combination_price_dataframe.copy()

            # Calculate Historical volatility data
            historical_volatility_value = calculate_hv(
                unique_id,
                variables.hv_method,
                combination_price_dataframe_for_hv,
                avg_price_combo,
            )

            # Annualized Historical Volatility  (this will be showed in the GUI)
            if variables.flag_enable_hv_annualized:

                if historical_volatility_value not in ["N/A", None]:

                    annualized_historical_volatility_value = (
                        historical_volatility_value
                        * math.sqrt(
                            variables.minutes_in_year / variables.hv_mins_in_candle
                        )
                    )

                else:

                    annualized_historical_volatility_value = "N/A"
            else:
                annualized_historical_volatility_value = historical_volatility_value

            if historical_volatility_value not in ["N/A", None]:

                # Candle Volatility
                candle_volatility_value = calculate_candle_volatility(
                    historical_volatility_value,
                    current_day_open_prices,
                    current_day_close_prices,
                    number_of_candles_since_day_open,
                )
            else:

                candle_volatility_value = "N/A"

            # Print to console
            if variables.flag_debug_mode:

                print(f"UniqueId: {unique_id}")
                print(
                    variables.hv_method.name
                    + " Annualized = "
                    + str(annualized_historical_volatility_value)
                )
                print(
                    variables.hv_method.name
                    + " Non-Annualized = "
                    + str(historical_volatility_value)
                )

            try:
                # Dict
                hv_values[unique_id] = {
                    "H. V.": annualized_historical_volatility_value,
                    "H.V. Without Annualized": historical_volatility_value,
                    "Candle Volatility": candle_volatility_value,
                }

            except Exception as e:
                print(f"Error inside of calculating HV Related columns : {e}")

            try:
                # Making it available via class variable
                variables.map_unique_id_to_hv_related_values[unique_id] = hv_values[
                    unique_id
                ]

            except Exception as e:
                print(f"Error inside of assigning HV Related columns values: {e}")

        # print(variables.map_unique_id_to_hv_related_values.keys())
        # print(variables.map_unique_id_to_hv_related_values)

    # Method to fetch historical prices for HV
    def get_historical_data_for_hv(
        self, cas_coinds_for_fetching_historical_data, hv_look_back_days, hv_candle_size
    ):

        # Info 'cas_coinds_for_fetching_historical_data' contains dict {coind : {BUY : 1H 1D ,  SELL: 1H 1D} }
        cas_coinds_for_fetching_historical_data = (
            cas_coinds_for_fetching_historical_data
        )

        # Duration String, user input max(cas_number_of_days and atr)
        duration_for_historical_data = hv_look_back_days

        # string for ibkr reqHistoricalData
        duration_size = f"{duration_for_historical_data} D"

        # Map of [conid][action][bar_size] = req_id
        map_conid_action_to_req_id = {}

        # List of all request ids
        req_id_list = []

        # To update long term values we need Daily Candles for which we need '1D' '1H' data.
        for conid, sub_info_dict in cas_coinds_for_fetching_historical_data.items():

            # Get Contract for conId
            contract = variables.map_con_id_to_contract[conid]

            # Create dict with conid as key
            if conid not in map_conid_action_to_req_id:
                map_conid_action_to_req_id[conid] = {}

            for action, sub_values in sub_info_dict.items():

                # Create dict with conid as key
                if action not in map_conid_action_to_req_id[conid]:
                    map_conid_action_to_req_id[conid][action] = None
                else:
                    continue

                # Get data for bar_size, if leg is active in all combinations
                for bar_size, sub_val in sub_values.items():

                    if sub_val > 0:

                        # Getting req_id from CAS APP
                        reqId = variables.cas_app.nextorderId
                        variables.cas_app.nextorderId += 1

                        # Map Historical Data ReqId to the dict
                        map_conid_action_to_req_id[conid][action] = reqId

                        # append reqid it to the list, will be used to check when all the data is available
                        req_id_list.append(reqId)

                        # candle / bar size for reqHistoricalData
                        bar_size = f"{hv_candle_size.value}"

                        # What to Show for reqHistoricalData
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

        # Counter for wait
        counter = 0

        # Keep Waiting for data till  'cas_wait_time_for_historical_data' time
        while variables.cas_wait_time_for_historical_data > (
            counter * variables.sleep_time_waiting_for_tws_response
        ):

            # dict_mkt_end = variables.req_mkt_data_end
            # dicterr_msg = variables.req_error
            #
            # merged_dict = {}
            #
            # for key in set(dict_mkt_end.keys()) | set(dicterr_msg.keys()):
            #     if key in dict_mkt_end and key in dicterr_msg:
            #         merged_dict[key] = dict_mkt_end[key] or dicterr_msg[key]
            #     elif key in dict_mkt_end:
            #         merged_dict[key] = dict_mkt_end[key]
            #     else:
            #         merged_dict[key] = dicterr_msg[key]
            #
            # # If reqHistorical Data ended for all the reqId
            # if all([merged_dict[req_id] for req_id in req_id_list]):
            #     break
            # If reqHistorical Data ended for all the reqId or Got Error for any of the reqId

            # if all([variables.req_mkt_data_end[req_id] for req_id in req_id_list]) or any(
            #         [variables.req_error[req_id] for req_id in req_id_list]
            # ):
            #     break

            # KARAN CHANGED IT - TODO - 20231027
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
