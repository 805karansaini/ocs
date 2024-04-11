import asyncio
import copy
import datetime
import math
import time

import pandas as pd

from com.variables import variables
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.indicators_calculator.helper_indicator import IndicatorHelper
from option_combo_scanner.indicators_calculator.historical_data_fetcher import HistoricalDataFetcher
from option_combo_scanner.indicators_calculator.indicator_hv_calculation import calculate_hv
from option_combo_scanner.strategy.strategy_variables import StrategyVariables
from option_combo_scanner.strategy.utilities import StrategyUtils


class HistoricalVolatility:
    scanner_hv_indicator_tab_obj = None

    def __init__(
        self,
    ):
        pass

    @staticmethod
    def get_all_underlying_for_which_data_is_required(
        local_map_indicator_id_to_indicator_object,
    ):
        """
        Returns map_underlying_conid_to_list_of_indicators_id as we need HV for underlying
        """

        map_conid_to_list_of_indicators_id = {}

        for (
            indicator_id,
            indicator_object,
        ) in local_map_indicator_id_to_indicator_object.items():
            underlying_conid = int(indicator_object.underlying_conid)
            indicator_id = int(indicator_id)

            if underlying_conid in map_conid_to_list_of_indicators_id:
                pass
            else:
                map_conid_to_list_of_indicators_id[underlying_conid] = []

            map_conid_to_list_of_indicators_id[underlying_conid].append(indicator_id)

        return map_conid_to_list_of_indicators_id

    @staticmethod
    def get_hv_calculation_for_each_conid(conid, merged_df):

        # Remaning columns
        merged_df = merged_df.rename(columns={"Open": "Combination Open", "Close": "Combination Close"})

        # Create new DataFrame with desired columns
        combination_price_dataframe = merged_df[["Time", "Combination Open", "Combination Close"]].copy()

        try:
            latest_combo_open = combination_price_dataframe.iloc[-1]["Combination Open"]
            latest_combo_close = combination_price_dataframe.iloc[-1]["Combination Close"]

            avg_price_combo = (latest_combo_open + latest_combo_close) / 2
        except Exception as e:

            # Print to console:
            if variables.flag_debug_mode:
                print(f"Could not compute the H. V. Related value. Exception {e}")

        # check if flag for calculating hv for daily candles is true
        if True: # StrategyVariables.flag_hv_daily:
            # Get dataframe with 1 D candles
            combination_price_dataframe_for_hv = HistoricalVolatility.group_dataframe_by_time_and_create_1d_candle_first_open_last_close(
                combination_price_dataframe.copy()
            )

        # # If flag for calculating hv for daily candles is false
        # else:
        #     combination_price_dataframe_for_hv = combination_price_dataframe.copy()

        # Calculate Historical volatility data
        historical_volatility_value = calculate_hv(
            conid,
            variables.hv_method,
            combination_price_dataframe_for_hv,
            avg_price_combo,
        )
        # print(f"HV STD: {historical_volatility_value}")

        # Annualized Historical Volatility  (this will be showed in the GUI)
        if True or variables.flag_enable_hv_annualized:

            if historical_volatility_value not in ["N/A", None]:

                # annualized_historical_volatility_value = historical_volatility_value * math.sqrt(variables.minutes_in_year / variables.hv_mins_in_candle)
                annualized_historical_volatility_value = historical_volatility_value * math.sqrt(255)

            else:

                annualized_historical_volatility_value = "N/A"
        else:
            annualized_historical_volatility_value = historical_volatility_value

        return annualized_historical_volatility_value

    # Used when calculating ATR and Correlation
    @staticmethod
    def group_dataframe_by_time_and_create_1d_candle_first_open_last_close(
        combo_open_close_df,
    ):
        # 'combo_open_close_df' will have Combination Open and Combination Close

        try:
            combo_open_close_df["Time"] = pd.to_datetime(combo_open_close_df["Time"])

            # group the data by date
            combo_open_close_df = combo_open_close_df.groupby(combo_open_close_df["Time"].dt.date)

            # define the aggregation functions
            agg_funcs = {"first", "last"}

            # apply the aggregation functions to each group
            combo_daily_open_close_df = combo_open_close_df["Combination Close"].agg(agg_funcs)

            # Converting multi-level columns to single-level columns
            combo_daily_open_close_df.columns = combo_daily_open_close_df.columns.map("".join)

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

        return combo_daily_open_close_df

    # Method to Fetch Historical Data
    @staticmethod
    def fetch_historical_data(map_conid_to_list_of_indicators_id, bar_size, duration_size, what_to_show):

        # Map of [conid][action] = req_id
        map_conid_to_req_id = {}

        # List of all request ids
        req_id_list = []

        for conid in map_conid_to_list_of_indicators_id:

            contract = StrategyVariables.map_con_id_to_contract[conid]
            # print(f"HV Contract: {contract}")
            what_to_show = what_to_show

            # Getting req_id
            reqId = variables.cas_app.nextorderId
            variables.cas_app.nextorderId += 1

            # Send the request
            HistoricalDataFetcher.request_historical_data_for_contract(contract, bar_size, duration_size, what_to_show, reqId)

            # append reqid it to the list
            req_id_list.append(reqId)

            # Map
            map_conid_to_req_id[conid] = reqId

        counter = 0
        while variables.cas_wait_time_for_historical_data > (counter * variables.sleep_time_waiting_for_tws_response):

            # KARAN CHANGED IT - TODO - 20231027
            if all([variables.req_mkt_data_end[req_id] or variables.req_error[req_id] for req_id in req_id_list]):
                break

            # Sleep for sleep_time_waiting_for_tws_response
            time.sleep(variables.sleep_time_waiting_for_tws_response)

            # Increase Counter
            counter += 1

        return map_conid_to_req_id

    @staticmethod
    def update_hv_calculation(conid, map_conid_to_list_of_indicators_id, values_dict):
        """
        "current_underlying_hv_value": current_underlying_hv_value,
        "average_underlying_hv_over_n_days": average_underlying_hv_over_n_days,
        "absoulte_change_in_underlying_over_n_days": absoulte_change_in_underlying_over_n_days,
        "percentage_change_in_underlying_over_n_days": percentage_change_in_underlying_over_n_days,
        """
        # List of Indicator IDs
        list_of_indicator_id = map_conid_to_list_of_indicators_id[conid]

        # Update the H.V. Value for indicator
        for indicator_id in list_of_indicator_id:
            # Update value in DB, Object & GUI
            IndicatorHelper.update_indicator_values_for_indcator_id(indicator_id=indicator_id, values_dict=values_dict)

        # print(f"Conid: {conid} Updated HV Values")

    @staticmethod
    def compute():
        """
        Basically does everything required to computes the indicator
        and returns the values
        """
        what_to_show = "BID"

        # Local local_map_indicator_id_to_indicator_object
        local_map_indicator_id_to_indicator_object = copy.deepcopy(StrategyVariables.map_indicator_id_to_indicator_object)

        # (Set, Minimize the request for historical data)AAPL Single: 5 Rows
        map_conid_to_list_of_indicators_id = HistoricalVolatility.get_all_underlying_for_which_data_is_required(
            local_map_indicator_id_to_indicator_object
        )

        # Fetch Historical data
        map_conid_to_req_id = HistoricalVolatility.fetch_historical_data(
            map_conid_to_list_of_indicators_id,
            StrategyVariables.bar_size_historical_volatility,
            StrategyVariables.duration_size_historical_volatility,
            what_to_show=what_to_show,
        )

        # get the dataframe for the req ID
        for con_id, req_id in map_conid_to_req_id.items():
            df = variables.map_req_id_to_historical_data_dataframe[req_id]

            # If Df is empty can not compute the values
            if df.empty:
                print(f"Unable to get the historical data for HV Calculation: {con_id}")
                continue

            # if flag is True Save CSV file
            if StrategyVariables.flag_store_csv_files:
                folder_name = "HistoricalVol"
                file_name = rf"{con_id}_complete"
                StrategyUtils.save_option_combo_scanner_csv_file(df, folder_name, file_name)

            # Convert the "Time" column to datetime format if it's not already in datetime format
            df["Time"] = pd.to_datetime(df["Time"])

            # Extract the date in YYYYMMDD format
            df["Date"] = df["Time"].dt.strftime("%Y%m%d")

            # Get the sorted list of unique dates in YYYYMMDD format
            unique_dates = sorted(list(set(df["Date"])))

            list_of_hv_values_for_n_days = []
            current_close_price = df.iloc[-1]["Close"]

            # Iterating and computing the HV for each day
            for indx in range(StrategyVariables.user_input_average_historical_volatility_days):

                # Start and End Date
                start_date = unique_dates[indx]
                end_date_indx = min(len(unique_dates) - 1, indx + StrategyVariables.user_input_average_historical_volatility_days - 1)
                end_date = unique_dates[end_date_indx]
                # print(f"Start Date {start_date} and End {end_date}")
                # Filter the dataframe
                filtered_df = df[(df["Date"] >= start_date) & (df["Date"] <= end_date)]

                try:
                    # Calculate the HV for the current day
                    if filtered_df.empty:
                        print(f"Filtered DataFrame Empty for HV")
                        continue
                    else:
                        # if flag is True Save CSV file
                        if StrategyVariables.flag_store_csv_files:
                            folder_name = rf"HistoricalVol\{con_id}"
                            file_name = (
                                rf"{StrategyVariables.user_input_average_historical_volatility_days - indx}_{start_date}_to_{end_date}"
                            )
                            StrategyUtils.save_option_combo_scanner_csv_file(filtered_df, folder_name, file_name)

                        hv_value = HistoricalVolatility.get_hv_calculation_for_each_conid(con_id, filtered_df)
                        if hv_value not in ["N/A", None]:
                            list_of_hv_values_for_n_days.append(hv_value)
                        else:
                            continue
                    if StrategyVariables.flag_test_print:
                        print(f"Day {indx} {start_date} to {end_date} HV: {hv_value}, having con_id: {con_id}")
                except Exception as e:
                    pass

            # Current HV
            current_underlying_hv_value = list_of_hv_values_for_n_days[-1] if len(list_of_hv_values_for_n_days) > 0 else None
            if StrategyVariables.flag_test_print:
                print(f"Current HV value for conid: {con_id},", current_underlying_hv_value)
            

            # Average HV over N-Days
            if len(list_of_hv_values_for_n_days) != 0:
                average_underlying_hv_over_n_days = sum(list_of_hv_values_for_n_days) / len(list_of_hv_values_for_n_days)
            else:
                # Handle the case where list_of_hv_values_for_n_days is empty
                average_underlying_hv_over_n_days = None
            # average_underlying_hv_over_n_days = sum(list_of_hv_values_for_n_days) / len(list_of_hv_values_for_n_days)
            # print(f"Average HV value ove n days for conid: {con_id},", average_underlying_hv_over_n_days)
            
            # Calculate Change in underlying
            n_day_ago_date = 14
            one_day_ago_date = 1 
            one_day_ago_date = unique_dates[-one_day_ago_date]
            n_day_ago_date = unique_dates[-n_day_ago_date]

            # 1_days_ago_close_price = COMPUTE from DF
            # Filter the DataFrame to get rows where Date matches date_var
            # If there are multiple rows for the same date, you can choose the first one
            filtered_df = df[df["Date"] == one_day_ago_date]
            one_day_ago_close_price = filtered_df["Close"].iloc[0]

            # n_days_ago_close_price = COMPUTE from DF
            # Filter the DataFrame to get rows where Date matches date_var
            # If there are multiple rows for the same date, you can choose the first one
            filtered_df = df[df["Date"] == n_day_ago_date]
            n_day_ago_close_price = filtered_df["Close"].iloc[0]

            try:
                absoulte_change_in_underlying_over_one_day = current_close_price - one_day_ago_close_price
                # print(f"Absolte chg in underlying over one day for conid: {con_id},", absoulte_change_in_underlying_over_one_day)
            except Exception as e:
                print(f"Exception Absolte chg in underlying over one day for conid {con_id} e: {e}")
                absoulte_change_in_underlying_over_one_day = None

            try:
                absoulte_change_in_underlying_over_n_days = current_close_price - n_day_ago_close_price
                # print(f"Absolte chg in underlying ove n days for conid: {con_id},", absoulte_change_in_underlying_over_n_days)
                percentage_change_in_underlying_over_n_days = ((current_close_price - n_day_ago_close_price) / n_day_ago_close_price) * 100
            except Exception as e:
                print(f"Exception Absolte chg in underlying ove n days for conid {con_id} e: {e}")
                absoulte_change_in_underlying_over_n_days = None
                percentage_change_in_underlying_over_n_days = None

            values_dict = {
                "absoulte_change_in_underlying_over_one_day": (
                    round(absoulte_change_in_underlying_over_one_day, 2)
                    if absoulte_change_in_underlying_over_one_day
                    else absoulte_change_in_underlying_over_one_day
                ),
                
                "absoulte_change_in_underlying_over_n_days": (
                    round(absoulte_change_in_underlying_over_n_days, 2)
                    if absoulte_change_in_underlying_over_n_days
                    else absoulte_change_in_underlying_over_n_days
                ),
                "percentage_change_in_underlying_over_n_days": (
                    round(percentage_change_in_underlying_over_n_days, 2)
                    if percentage_change_in_underlying_over_n_days
                    else percentage_change_in_underlying_over_n_days
                ),
                "current_underlying_hv_value": (
                    round(current_underlying_hv_value, 2) if current_underlying_hv_value else current_underlying_hv_value
                ),
                "average_underlying_hv_over_n_days": (
                    round(average_underlying_hv_over_n_days, 2) if average_underlying_hv_over_n_days else average_underlying_hv_over_n_days
                ),
            }

            # Updating the HV and Avg HV ove N-Days for all the indicator having the same underlying
            HistoricalVolatility.update_hv_calculation(con_id, map_conid_to_list_of_indicators_id, values_dict)
