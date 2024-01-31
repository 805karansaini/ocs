"""
Created on 08-Jun-2023

@author: ashish
"""


from com.variables import *
from com.high_low_price_calculator import *
from com.prices import *
from com.hv_calculation import *
from com.user_inputs import *
from com.high_low_cal_helper import *


class VolumeRelated:
    def __init__(self):
        pass

    # Method to fetch historical data for combination
    def get_historical_volume_for_all_combinations(
        self,
        cas_coinds_for_fetching_historical_data,
        duration_size="1 D",
        bar_size="1 min",
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

    # Calcualte combo volume based on leg volume
    def calculate_volume_contribution_of_legs(
        self, row, volume, all_data_frames, factors
    ):
        value = 0

        for leg_no in range(len(all_data_frames)):

            column_name = f"{volume} {leg_no + 1}"

            value += float(row[column_name]) / factors[leg_no]
        return value

    # Method to calculate average and standard deviation of volume
    def calculate_mean_and_std_for_combination_volume(
        self, combination_volume_dataframe
    ):

        mean_for_net_volume = combination_volume_dataframe["Combination Volume"].mean()
        standard_deviation_for_net_volume = combination_volume_dataframe[
            "Combination Volume"
        ].std()

        return mean_for_net_volume, standard_deviation_for_net_volume

    # Calculate relative_change_value / relative_volume_value
    def calculate_relative_change_div_relative_volume(
        self, relative_change_value, relative_volume_value
    ):
        try:
            relative_change_div_Relative_volume_value = (
                relative_change_value / relative_volume_value
            )
        except Exception as e:
            relative_change_div_Relative_volume_value = "N/A"
            print(
                f"Inside of calculating 'calculate_relative_change_div_Relative_volume', error is {e}"
            )

    # Calculate average of combinational volume for given dataframe
    def calculate_sum_volume_for_dataframe(self, combinational_volume_dataframe):

        try:
            # Calculate mean of combinational volume column
            average_volume_for_dataframe_value = combinational_volume_dataframe[
                "Combination Volume"
            ].sum()
        except Exception as e:
            print(f"Inside calculate average volume for dataframe , error is {e}")
        return average_volume_for_dataframe_value

    # Calculate Volume since start of the day / Average Volume for the same time-period averaged over the look back
    def calculate_relative_volume(
        self,
        unique_id,
        latest_day_dataframe,
        historical_data_except_current_day_dataframe,
        date_time_start,
        date_time_close,
    ):

        # Convert the 'Time' column to datetime type if it's not already
        historical_data_except_current_day_dataframe["Time"] = pd.to_datetime(
            historical_data_except_current_day_dataframe["Time"]
        )

        # Filter the rows where the time is between start and end time
        filtered_historical_data_dataframe = (
            historical_data_except_current_day_dataframe[
                (
                    historical_data_except_current_day_dataframe["Time"].dt.time
                    >= pd.to_datetime(date_time_start).time()
                )
                & (
                    historical_data_except_current_day_dataframe["Time"].dt.time
                    <= pd.to_datetime(date_time_close).time()
                )
            ].reset_index(drop=True)
        )

        # Calculate Volume since start of the day
        volume_since_start_of_day = self.calculate_sum_volume_for_dataframe(
            latest_day_dataframe
        )

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
            if variables.flag_store_cas_tab_csv_files:

                file_path = rf"{variables.cas_tab_csv_file_path}\Volume\RelativeVolume"

                if not os.path.exists(file_path):
                    os.makedirs(file_path)

                # Saving CSV
                date_specific_dataframe_for_volume.to_csv(
                    rf"{file_path}\{unique_id}_relv_volume_{date_ith}.csv", index=False
                )

            # Calculating the average volume for each day in lookback period
            calculated_volume_for_look_back_days.append(
                self.calculate_sum_volume_for_dataframe(
                    date_specific_dataframe_for_volume
                )
            )

        try:
            # Calculate Avg volume for the same time period averaged over the look back
            volume_avg_over_lookback_period = sum(
                calculated_volume_for_look_back_days
            ) / len(calculated_volume_for_look_back_days)

            # calculate Volume since start of the day / Average Volume for the same time-period averaged over the look back
            relative_volume = round(
                volume_since_start_of_day / volume_avg_over_lookback_period, 2
            )
        except Exception as e:

            # Print to console
            if variables.flag_debug_mode:
                print(
                    f"Calculating Realtive volume 'calculate_relative_volume' Exception: {e}"
                )

            relative_volume = "N/A"

        return relative_volume

    # Method to merger dataframe to get final volume data
    def merge_dataframe_inner_join_with_combo_net_volume_calculation(
        self, combo_obj, all_data_frames
    ):

        # All legs  in combo
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

            # +ve factor for both actions
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

    # Method to calculate volume related fields
    def calculate_volume_related_fields(
        self, local_unique_id_to_combo_obj, map_conid_to_req_id
    ):

        # Dict
        local_map_unique_id_to_volume_related_fields = {}
        current_volume = {}

        for unique_id, combo_obj in local_unique_id_to_combo_obj.items():

            local_map_unique_id_to_volume_related_fields[unique_id] = {
                "Mean of Net Volume": "N/A",
                "STD +1": "N/A",
                "STD -1": "N/A",
                "STD +2": "N/A",
                "STD -2": "N/A",
                "STD +3": "N/A",
                "STD -3": "N/A",
            }

            current_volume[unique_id] = "N/A"

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
            if variables.flag_store_cas_tab_csv_files:

                for i, df_xxx in enumerate(all_data_frames):

                    file_path = rf"{variables.cas_tab_csv_file_path}\Volume"
                    file_path += rf"\Leg_Wise\Unique_id_{unique_id}"

                    if not os.path.exists(file_path):
                        os.makedirs(file_path)

                    df_xxx.to_csv(rf"{file_path}\Leg_{i+1}_Volume.csv", index=False)

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
                local_map_unique_id_to_volume_related_fields[unique_id] = {
                    "Mean of Net Volume": "N/A",
                    "STD +1": "N/A",
                    "STD -1": "N/A",
                    "STD +2": "N/A",
                    "STD -2": "N/A",
                    "STD +3": "N/A",
                    "STD -3": "N/A",
                }
                current_volume[unique_id] = "N/A"

                continue

            # Merging the data frame, inner join on time
            merged_df = (
                self.merge_dataframe_inner_join_with_combo_net_volume_calculation(
                    combo_obj, all_data_frames
                )
            )

            # Save DF to CSV File
            if variables.flag_store_cas_tab_csv_files:

                # Saving dataframe to csv
                file_path = rf"{variables.cas_tab_csv_file_path}\Volume\Merged"

                if not os.path.exists(file_path):
                    os.makedirs(file_path)

                merged_df.to_csv(
                    rf"{file_path}\Unique_Id_{unique_id}_volume_all_legs_merged.csv",
                    index=False,
                )

            # Create new DataFrame with desired columns
            combination_net_volume_dataframe = merged_df[
                [
                    "Time",
                    "Combination Volume",
                ]
            ].copy()

            try:

                # get current volume
                current_volume_val = combination_net_volume_dataframe[
                    "Combination Volume"
                ].iloc[-1]

                current_volume[unique_id] = current_volume_val

                # Getting the Mean and the STD volume for the combination
                (
                    mean_of_net_volume,
                    standard_deviation_of_net_volume,
                ) = self.calculate_mean_and_std_for_combination_volume(
                    combination_net_volume_dataframe
                )

                local_map_unique_id_to_volume_related_fields[unique_id] = {
                    "Mean of Net Volume": mean_of_net_volume,
                    "STD +1": mean_of_net_volume
                    + (+1 * standard_deviation_of_net_volume),
                    "STD -1": mean_of_net_volume
                    + (-1 * standard_deviation_of_net_volume),
                    "STD +2": mean_of_net_volume
                    + (+2 * standard_deviation_of_net_volume),
                    "STD -2": mean_of_net_volume
                    + (-2 * standard_deviation_of_net_volume),
                    "STD +3": mean_of_net_volume
                    + (+3 * standard_deviation_of_net_volume),
                    "STD -3": mean_of_net_volume
                    + (-3 * standard_deviation_of_net_volume),
                }

                # Making it available via class variable
                variables.map_unique_id_to_volume_related_fields[
                    unique_id
                ] = local_map_unique_id_to_volume_related_fields[unique_id]

            except Exception as e:
                print(f"Error inside of assigning Volume Related columns values: {e}")

        # Setting updated value in the variables dict
        # variables.map_unique_id_to_volume_related_fields = local_map_unique_id_to_volume_related_fields

        return local_map_unique_id_to_volume_related_fields, current_volume

    # Method to manage volume related values
    def update_volume_related_fields(self, conid_list=None, unique_id_added=None):

        # Getting lookback days and candle size for historical data related to volume (Formatting the lookback)
        duration_size = f"{variables.volume_related_fileds_look_back_days} D"
        bar_size = f"{variables.volume_related_fileds_candle_size.value}"

        # Get all the Active Combinations ( unique, combo_ob), local copy of 'unique_id_to_combo_obj'
        local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

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

        # Getting Volume for all the combinations
        map_conid_to_req_id = self.get_historical_volume_for_all_combinations(
            cas_coinds_for_fetching_historical_data, duration_size, bar_size
        )

        # MERGED DATAFRAME FOR COMBVINATION
        # WE WANT ALL THE CALCULATED VALUES (NET VOLU STD1, )
        (
            map_unique_id_to_volume_related_fields,
            _,
        ) = self.calculate_volume_related_fields(
            local_unique_id_to_combo_obj, map_conid_to_req_id
        )

        # variables.map_unique_id_to_volume_related_fields = map_unique_id_to_volume_related_fields
        # COMUTE VALUES

    # Method to get volume magnet timestamp
    def get_volume_magnet_tiestamps(self, conid_list=None, unique_id_added=None):

        # Get all the Active Combinations ( unique, combo_ob), local copy of 'unique_id_to_combo_obj'
        local_unique_id_to_combo_obj = copy.deepcopy(variables.unique_id_to_combo_obj)

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

        # Init flag
        flag_volume_level_found = False

        # Init lookback days
        volume_magnet_lookback_days = 0

        # Continue loop till we get all volume magnet
        while not flag_volume_level_found:

            # add lookback days
            volume_magnet_lookback_days += 5

            # Check if lookback day exceeds max lookback days
            if volume_magnet_lookback_days > variables.volume_magnet_max_lookback_days:
                break

            # To get lookback we needed to get all  volume magnet values
            variables.volume_magnet_final_lookback_days = volume_magnet_lookback_days

            # Getting lookback days and candle size for historical data related to volume (Formatting the lookback)
            duration_size = f"{volume_magnet_lookback_days} D"
            bar_size = f"{variables.volume_magnet_candle_size.value}"

            # Getting Volume for all the combinations
            map_conid_to_req_id = self.get_historical_volume_for_all_combinations(
                cas_coinds_for_fetching_historical_data, duration_size, bar_size
            )

            # Check if we found relavant volume for volume magnet
            flag_volume_level_found_dict = self.check_volume_occurence(
                local_unique_id_to_combo_obj, map_conid_to_req_id
            )

            try:

                # set flag to true
                flag_volume_level_found = True

                # Check flag for eah unique id
                for unique_id in flag_volume_level_found_dict:

                    # if flag for unique id is false
                    if not flag_volume_level_found_dict[unique_id]:

                        # set value to false
                        flag_volume_level_found = False

                        break

            except Exception as e:
                if variables.flag_debug_mode:

                    print(e)
                # Print to console
                if variables.flag_debug_mode:
                    print(f"Error inside volume magnet, Exp: {e}")

    # Method to check volume occurence in past data
    def check_volume_occurence(self, local_unique_id_to_combo_obj, map_conid_to_req_id):

        # Init dict
        flag_is_volume_greater_or_equal_to = {}

        # Iterate uique ids
        for unique_id, combo_obj in local_unique_id_to_combo_obj.items():

            # Get all legs
            buy_legs = combo_obj.buy_legs
            sell_legs = combo_obj.sell_legs
            all_legs = buy_legs + sell_legs

            # set default value to 'N/A'
            variables.volume_magnet_time_stamp[unique_id] = "N/A"

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
            # check if df is empty
            if is_data_frame_empty:

                continue

            # Merging the data frame, inner join on time
            merged_df = (
                self.merge_dataframe_inner_join_with_combo_net_volume_calculation(
                    combo_obj, all_data_frames
                )
            )

            try:

                # get current volume value
                current_volume_val = float(merged_df["Combination Volume"].iloc[-1])

            except Exception as e:

                current_volume_val = 'N/A'

            """list_of_volumes = []

            
            # Processing "Buy" Legs to calculate prices
            for leg_obj in all_legs:
                # get conid
                con_id = leg_obj.con_id

                # get req id
                req_id = variables.con_id_to_req_id_dict[con_id]

                # get bid qty for sell legs
                volume_of_leg = variables.volume[req_id]

                # we are dividing it by the 1/100 here.
                multiplier = (1 / 100) if leg_obj.sec_type == 'STK' else 1

                # +ve factor for both actions
                factor = leg_obj.quantity * multiplier

                volume_of_leg = volume_of_leg / factor

                list_of_volumes.append(volume_of_leg)

            combo_volume = sum(list_of_volumes) / len(list_of_volumes)
            print(combo_volume)"""

            # Remove the last row
            merged_df = merged_df.drop(merged_df.index[-1])
            # print(merged_df.tail())

            # Save DF to CSV File
            if variables.flag_store_cas_tab_csv_files:

                file_path = rf"{variables.cas_tab_csv_file_path}\Volume Magnet\Volume"
                file_path += rf"\Unique_id_{unique_id}"

                if not os.path.exists(file_path):
                    os.makedirs(file_path)

                merged_df.to_csv(
                    rf"{file_path}\Unique_ID_{unique_id}_Volume_magnet_volume_df.csv",
                    index=False,
                )

            # Check if all values in column 'A' are greater than 10
            flag_is_volume_greater_or_equal_to[unique_id] = (
                merged_df["Combination Volume"] >= current_volume_val
            ).any()

            # set default value to 'N/A'
            most_recent_timestamp = "N/A"

            # set default value to 'N/A'
            variables.volume_magnet_time_stamp[unique_id] = most_recent_timestamp

            # check if there is volume greater or equal to current
            if flag_is_volume_greater_or_equal_to[unique_id]:

                # Get the most recent timestamp where combo volume is greater than current volume
                most_recent_timestamp = merged_df.loc[
                    merged_df["Combination Volume"] >= current_volume_val, "Time"
                ].max()

                # set value in global dict
                variables.volume_magnet_time_stamp[unique_id] = most_recent_timestamp

        return flag_is_volume_greater_or_equal_to
