import asyncio
import copy
import datetime
import math
import time

import pandas as pd

from com.variables import variables
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.indicators_calculator.historical_data_fetcher import (
    HistoricalDataFetcher,
)
from option_combo_scanner.indicators_calculator.indicator_hv_calculation import (
    calculate_hv,
)
from option_combo_scanner.strategy.indicator import Indicator
from option_combo_scanner.strategy.strategy_variables import StrategyVariables
from option_combo_scanner.strategy.zzz_deprc_aryan_scanner import Scanner


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
    def compute():
        """
        Basically does everything required to computes the indicator
        and returns the values
        """
        # look_back = "28 D"
        # what_to_show = "BID"
        # candle_size = "2 H"

        # Local local_map_indicator_id_to_indicator_object
        local_map_indicator_id_to_indicator_object = copy.deepcopy(
            StrategyVariables.map_indicator_id_to_indicator_object
        )

        # (Set, Minimize the request for historical data)AAPL Single: 5 Rows
        map_conid_to_list_of_indicators_id = (
            HistoricalVolatility.get_all_underlying_for_which_data_is_required(
                local_map_indicator_id_to_indicator_object
            )
        )

        # Fetch Historical data
        map_conid_to_req_id = HistoricalVolatility.fetch_historical_data(
            map_conid_to_list_of_indicators_id,
            StrategyVariables.bar_size_historical_volatility,
            StrategyVariables.duration_size_historical_volatility,
        )

        # get the dataframe for the req ID
        for con_id, req_id in map_conid_to_req_id.items():
            df = variables.map_req_id_to_historical_data_dataframe[req_id]

            if df is not None:
                print(f"Saving the df for conind: {con_id}")
                df.to_csv(rf"Temp\{con_id}.csv")
            else:
                print(f"DataFrame is empty")

            df["Time"] = pd.to_datetime(df["Time"])

            hv_values = []
            for day in range(1, 15):
                start_date = pd.Timestamp.now(tz="Israel").normalize() - pd.Timedelta(
                    days=day + 14
                )
                end_date = pd.Timestamp.now(tz="Israel").normalize() - pd.Timedelta(
                    days=day
                )
                # print(f"{day} Day(s) old HV: Lookback/Period 14 Days: Data: {start_date.date()} - {end_date.date()}")

                filtered_df = df[(df["Time"] >= start_date) & (df["Time"] <= end_date)]

                try:
                    # Calculate the HV for the current day
                    if not filtered_df.empty:
                        hv_value = (
                            HistoricalVolatility.get_hv_calculation_for_each_conid(
                                con_id, filtered_df
                            )
                        )
                        if hv_value not in ["N/A"]:
                            hv_values.append(hv_value)

                    # print(f"Day {day} HV: {hv_value}")
                except Exception as e:
                    print(e)

            try:
                hv_value = HistoricalVolatility.get_hv_calculation_for_each_conid(
                    con_id, df
                )
                # print(f"Indicator Conid: {con_id} H. V.: {hv_value}")
            except Exception as e:
                print(e)
            # print("avghv", hv_values)

            # HV(14D)-Avg(14D)
            hv_14d_avg_14d = sum(hv_values) / len(hv_values)
            # print("HV_Value Avg14D", hv_14d_avg_14d)

            # HV(14D)-AvgIV

            HistoricalVolatility.update_hv_calculation(
                con_id, hv_value, hv_14d_avg_14d, map_conid_to_list_of_indicators_id
            )

    @staticmethod
    def update_hv_calculation(
        conid, hv_value, hv_14d_avg_14d, map_conid_to_list_of_indicators_id
    ):
        list_of_indicator_id = map_conid_to_list_of_indicators_id[conid]

        values_dict = {
            "hv": hv_value,
            "hv_14d_avg_14d": hv_14d_avg_14d,
        }
        where_condition = f" WHERE `underlying_conid` = {conid};"

        select_query = SqlQueries.create_update_query(
            table_name="indicator_table",
            values_dict=values_dict,
            where_clause=where_condition,
        )
        # Get all the old rows from indicator table
        res = SqlQueries.execute_update_query(select_query)

        if not res:
            print(f"HV values not updated in DB", {conid})
            # return

        for indicator_id in list_of_indicator_id:

            if indicator_id in StrategyVariables.map_indicator_id_to_indicator_object:
                StrategyVariables.map_indicator_id_to_indicator_object[
                    indicator_id
                ].hv = hv_value
                StrategyVariables.map_indicator_id_to_indicator_object[
                    indicator_id
                ].hv_14d_avg_14d = hv_14d_avg_14d

                StrategyVariables.scanner_indicator_table_df.loc[
                    StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                    == indicator_id,
                    "hv",
                ] = hv_value
                StrategyVariables.scanner_indicator_table_df.loc[
                    StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                    == indicator_id,
                    "hv_14d_avg_14d",
                ] = hv_14d_avg_14d

            else:
                print(f"Indicator object not found for conid: {conid}")

            # print(StrategyVariables.scanner_indicator_table_df.to_string())
            HistoricalVolatility.scanner_hv_indicator_tab_obj.update_into_indicator_table(
                StrategyVariables.scanner_indicator_table_df
            )

    @staticmethod
    def get_hv_calculation_for_each_conid(conid, merged_df):

        # HV HV without Annualized
        # merged_df.rename(columns={'Open': 'Combination Open', 'Close': 'Combination Close'}, inplace=True)
        merged_df = merged_df.rename(
            columns={"Open": "Combination Open", "Close": "Combination Close"}
        )

        # Create new DataFrame with desired columns
        combination_price_dataframe = merged_df[
            ["Time", "Combination Open", "Combination Close"]
        ].copy()

        try:
            latest_combo_open = combination_price_dataframe.iloc[-1]["Combination Open"]
            latest_combo_close = combination_price_dataframe.iloc[-1][
                "Combination Close"
            ]

            avg_price_combo = (latest_combo_open + latest_combo_close) / 2
        except Exception as e:

            # Print to console:
            if variables.flag_debug_mode:
                print(f"Could not compute the H. V. Related value. Exception {e}")

        # check if flag for calculating hv for daily candles is true
        if variables.flag_hv_daily:

            # Get dataframe with 1 D candles
            combination_price_dataframe_for_hv = HistoricalVolatility.group_dataframe_by_time_and_create_1d_candle_first_open_last_close(
                combination_price_dataframe.copy()
            )

        # If flag for calculating hv for daily candles is false
        else:

            combination_price_dataframe_for_hv = combination_price_dataframe.copy()

        # Calculate Historical volatility data
        historical_volatility_value = calculate_hv(
            conid,
            variables.hv_method,
            combination_price_dataframe_for_hv,
            avg_price_combo,
        )

        # Annualized Historical Volatility  (this will be showed in the GUI)
        if variables.flag_enable_hv_annualized:

            if historical_volatility_value not in ["N/A", None]:

                annualized_historical_volatility_value = (
                    historical_volatility_value
                    * math.sqrt(variables.minutes_in_year / variables.hv_mins_in_candle)
                )

            else:

                annualized_historical_volatility_value = "N/A"
        else:
            annualized_historical_volatility_value = historical_volatility_value

        # Print to console
        if variables.flag_debug_mode:

            print(f"Indicator Conid: {conid}")
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

    # Method to Fetch Historical Data
    @staticmethod
    def fetch_historical_data(
        map_conid_to_list_of_indicators_id, bar_size, duration_size
    ):

        # Map of [conid][action] = req_id
        map_conid_to_req_id = {}

        # List of all request ids
        req_id_list = []

        for conid in map_conid_to_list_of_indicators_id:

            contract = StrategyVariables.map_con_id_to_contract[conid]

            # TODO
            what_to_show = "BID"

            # Getting req_id
            reqId = variables.cas_app.nextorderId
            variables.cas_app.nextorderId += 1

            # Send the request
            HistoricalDataFetcher.request_historical_data_for_contract(
                contract, bar_size, duration_size, what_to_show, reqId
            )

            # append reqid it to the list
            req_id_list.append(reqId)

            # Map
            map_conid_to_req_id[conid] = reqId

        counter = 0
        while variables.cas_wait_time_for_historical_data > (
            counter * variables.sleep_time_waiting_for_tws_response
        ):

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

        return map_conid_to_req_id
