import asyncio
import copy
import datetime
import time

import numpy as np
import pandas as pd
from tabulate import tabulate

from com.contracts import get_contract
from com.option_comobo_scanner_idetif import (
    find_closest_expiry_for_fop_given_fut_expiries_and_trading_class,
    find_nearest_expiry_and_all_strikes_for_stk_given_dte,
    find_nearest_expiry_for_future_given_fut_dte,
)

# from com import variables
from com.variables import variables
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.greeks import (
    get_underlying_implied_volatility_and_cmp,
)
from option_combo_scanner.indicators_calculator.helper_indicator import IndicatorHelper
from option_combo_scanner.indicators_calculator.historical_data_fetcher import (
    HistoricalDataFetcher,
)
from option_combo_scanner.indicators_calculator.historical_volatility import (
    HistoricalVolatility,
)
from option_combo_scanner.indicators_calculator.market_data_fetcher import (
    MarketDataFetcher,
)
from option_combo_scanner.strategy.strategy_variables import StrategyVariables
from option_combo_scanner.strategy.utilities import StrategyUtils


class PutCallVol:
    scanner_indicator_tab_pc_obj = None

    def __init__(self):
        pass

    @staticmethod
    def create_daily_candle_df_from_raw_df(df):
        df_daily_sum = pd.DataFrame()
        try:
            # Convert 'date' column to datetime if it's not already in datetime format
            df["Time"] = pd.to_datetime(df["Time"])

            # Extract unique dates and initialize lists to store aggregated values
            unique_dates = df["Time"].dt.date.unique()

            # Array for values
            open_values = []
            close_values = []
            vol_values = []

            # Iterate over unique dates and aggregate 'open' and 'close' values
            for date_ in unique_dates:
                filtered_df = df[df["Time"].dt.date == date_]

                open_sum = filtered_df["Open"].sum()
                close_sum = filtered_df["Close"].sum()
                vol_sum = filtered_df["Volume"].sum()
                open_values.append(open_sum)
                close_values.append(close_sum)
                vol_values.append(vol_sum)

            # Create a new DataFrame with aggregated values for each date
            df_daily_sum = pd.DataFrame(
                {
                    "Date": unique_dates,
                    "Open": open_values,
                    "Close": close_values,
                    "Volume": vol_values,
                }
            )
        except Exception as e:
            print(
                f"Inside PutCallVol: create_daily_candle_df_from_raw_df Exception {e}"
            )

        return df_daily_sum

    @staticmethod
    def get_total_vol_for_date(
        date, call_list_of_daily_volume_data_df, put_list_of_daily_volume_data_df
    ):
        total_call_vol_for_date = 0
        total_put_vol_for_date = 0

        # Iterate through call_list_of_daily_volume_data_df and put_list_of_daily_volume_data_df to find volumes for the given date
        for call_df_for_strike_s in call_list_of_daily_volume_data_df:
            # Get vol for date
            if not call_df_for_strike_s.empty:
                vol_for_date = call_df_for_strike_s[
                    call_df_for_strike_s["Date"] == date
                ]["Volume"].sum()
                total_call_vol_for_date += float(vol_for_date)

        for put_df_for_strike_s in put_list_of_daily_volume_data_df:
            if not put_df_for_strike_s.empty:
                vol_for_date = put_df_for_strike_s[put_df_for_strike_s["Date"] == date][
                    "Volume"
                ].sum()
                total_put_vol_for_date += float(vol_for_date)

        return total_call_vol_for_date, total_put_vol_for_date

    @staticmethod
    def compute(
        indicator_object,
        symbol,
        expiry,
        sec_type,
        underlying_sec_type,
        exchange,
        currency,
        multiplier,
        trading_class,
        underlying_contract,
        all_strikes,
        flag_put_call_indicator_based_on_selected_deltas_only=False,
        list_of_all_call_strikes=None,
        list_of_all_put_strikes=None,
    ):
        """
        Indicator Row:
            m. Put/Call Volume Ratio:
            n. Put/Call Volume Ratio Average Over NDays:
            u. PC Change only  (PC Change / I.V. Change:
        """

        # Instrument ID
        indicator_id = indicator_object.indicator_id
        instrument_id = indicator_object.instrument_id

        # Check for early termination
        if Utils.flag_check_early_termination_of_indicator(
            indicator_id=indicator_id, instrument_id=instrument_id
        ):
            return

        if not flag_put_call_indicator_based_on_selected_deltas_only:
            # Get the current date
            current_date_for_dte = datetime.datetime.today().strftime("%Y%m%d")
            current_date_obj_for_dte = datetime.datetime.strptime(
                current_date_for_dte, "%Y%m%d"
            )
            expiry_date_obj_for_dte = datetime.datetime.strptime(expiry, "%Y%m%d")

            dte = abs(current_date_obj_for_dte - expiry_date_obj_for_dte).days

            # Getting the underlying_contarct, and all the call and put option contracts
            (
                list_of_all_call_option_contracts,
                list_of_all_put_option_contracts,
            ) = IndicatorHelper.get_list_of_call_and_put_option_contracts(
                symbol,
                sec_type,
                expiry,
                dte,
                underlying_sec_type,
                exchange,
                currency,
                multiplier,
                trading_class,
                all_strikes,
            )
        else:
            list_of_all_call_option_contracts = []
            list_of_all_put_option_contracts = []

            for strike in list_of_all_call_strikes:
                # Sec Type for IND Support gets OPT
                if sec_type == "IND":
                    sec_type = "OPT"
                    exchange = "SMART"

                opt_contract = get_contract(
                    symbol=symbol,
                    sec_type=sec_type,
                    exchange=exchange,
                    currency=currency,
                    expiry_date=expiry,
                    strike_price=strike,
                    right="CALL",
                    multiplier=multiplier,
                    trading_class=trading_class,
                )
                list_of_all_call_option_contracts.append(opt_contract)

            for strike in list_of_all_put_strikes:
                # Sec Type for IND Support gets OPT
                if sec_type == "IND":
                    sec_type = "OPT"
                    exchange = "SMART"

                opt_contract = get_contract(
                    symbol=symbol,
                    sec_type=sec_type,
                    exchange=exchange,
                    currency=currency,
                    expiry_date=expiry,
                    strike_price=strike,
                    right="PUT",
                    multiplier=multiplier,
                    trading_class=trading_class,
                )
                list_of_all_put_option_contracts.append(opt_contract)

        # Check for early termination
        if Utils.flag_check_early_termination_of_indicator(
            indicator_id=indicator_id, instrument_id=instrument_id
        ):
            return

        # WE WANT HISTORICAL DATA what_to_show = TRADES
        what_to_show = "TRADES"

        list_of_daily_volume_data_df_for_call = []
        list_of_daily_volume_data_df_for_put = []

        list_right_and_list_contracts_tuple = [
            ("Call", list_of_all_call_option_contracts),
            ("Put", list_of_all_put_option_contracts),
        ]

        # Fetch Historical data
        for right, list_option_contracts in list_right_and_list_contracts_tuple:
            # print(f"PC VOlumne: {right}, {list_option_contracts}")

            list_of_contracts = list_option_contracts

            # Get From Variables
            bar_size = StrategyVariables.put_call_volume_bar_size
            duration_size = StrategyVariables.put_call_volume_lookback_days

            list_of_duration_size_for_fetcher = [duration_size] * len(list_of_contracts)

            list_of_req_id_for_historical_data = (
                HistoricalDataFetcher.fetch_historical_data_for_list_of_contracts(
                    list_of_contracts,
                    bar_size,
                    list_of_duration_size_for_fetcher,
                    what_to_show,
                )
            )

            # Historical Data for N-Days now we can need to create daily candles
            for req_id, contract in zip(
                list_of_req_id_for_historical_data, list_of_contracts
            ):
                df = variables.map_req_id_to_historical_data_dataframe[req_id]

                if df.empty:
                    # print(f"ReqId: {req_id}: Right:{right} empty")
                    continue
                # else:
                # print(f"ReqId: {req_id}: Right:{right} {df.shape}")

                daily_volume_data_df = PutCallVol.create_daily_candle_df_from_raw_df(df)

                if right == "Call":
                    list_of_daily_volume_data_df_for_call.append(daily_volume_data_df)
                    if StrategyVariables.flag_store_csv_files:
                        folder_name = (
                            rf"PutCallVol\{indicator_object.indicator_id}\Call"
                        )
                        file_name = rf"Call_{contract.strike}"
                        StrategyUtils.save_option_combo_scanner_csv_file(
                            daily_volume_data_df, folder_name, file_name
                        )

                else:
                    list_of_daily_volume_data_df_for_put.append(daily_volume_data_df)
                    if StrategyVariables.flag_store_csv_files:
                        folder_name = rf"PutCallVol\{indicator_object.indicator_id}\Put"
                        file_name = rf"Put_{contract.strike}"
                        StrategyUtils.save_option_combo_scanner_csv_file(
                            daily_volume_data_df, folder_name, file_name
                        )

            # Check for early termination
            if Utils.flag_check_early_termination_of_indicator(
                indicator_id=indicator_id, instrument_id=instrument_id
            ):
                return

        # Map to store total volume for Call and Put
        map_date_to_total_put_volume = {}
        map_date_to_total_call_volume = {}
        map_date_to_put_call_volume_ratio = {}

        # Get the Sorted Date Set, In Latest to Oldest Value manner
        if (
            list_of_daily_volume_data_df_for_call
            and list_of_daily_volume_data_df_for_put
        ):
            list_of_daily_volume_data_df_of_combined_call_and_put = (
                list_of_daily_volume_data_df_for_call
                + list_of_daily_volume_data_df_for_put
            )
            all_dates = pd.concat(
                [
                    df["Date"]
                    for df in list_of_daily_volume_data_df_of_combined_call_and_put
                    if not df.empty
                ]
            )
        else:
            return

        sorted_dates = sorted(all_dates.drop_duplicates(), reverse=True)
        sorted_dates_set = sorted(list(set(sorted_dates)), reverse=True)

        latest_date = sorted_dates_set[0]

        # print(f"Indicaor ID: {indicator_object.indicator_id}")

        for date in sorted_dates_set:
            # Get the total volume for Call and Put
            (
                total_call_vol_for_date,
                total_put_vol_for_date,
            ) = PutCallVol.get_total_vol_for_date(
                date,
                list_of_daily_volume_data_df_for_call,
                list_of_daily_volume_data_df_for_put,
            )

            map_date_to_total_put_volume[date] = total_put_vol_for_date
            map_date_to_total_call_volume[date] = total_call_vol_for_date

            # Calculate the put-call volume ratio
            if total_put_vol_for_date and total_call_vol_for_date != 0:
                put_call_volum_ratio = total_put_vol_for_date / total_call_vol_for_date
            else:
                put_call_volum_ratio = None  # Handle division by zero case
            if StrategyVariables.flag_test_print:
                print(
                    f"Date: {date}  PutVolume: {total_put_vol_for_date} CallVolume: {total_call_vol_for_date} PCRatio: {put_call_volum_ratio}"
                )

            # Store the put-call volume ratio for the date
            map_date_to_put_call_volume_ratio[date] = put_call_volum_ratio

        # Check for early termination
        if Utils.flag_check_early_termination_of_indicator(
            indicator_id=indicator_id, instrument_id=instrument_id
        ):
            return

        # Make Sure length of dict >= 2  sorted_dates_set
        put_call_volume_ratio_current_day = map_date_to_put_call_volume_ratio[
            latest_date
        ]

        # Remove None PC Ration from the dict
        total_pc_ratio_value = 0
        pc_ratio_count = 0
        for k, v in map_date_to_put_call_volume_ratio.items():
            if v:
                total_pc_ratio_value += v
                pc_ratio_count += 1

        put_call_volume_ratio_average_over_n_days = (
            total_pc_ratio_value / pc_ratio_count
            if pc_ratio_count not in [None, 0]
            else None
        )
        if StrategyVariables.flag_test_print:
            print(f"Current P/C Ratio Current: ", put_call_volume_ratio_current_day)
            print(
                f"P/C Ratio Average Over N-Days: ",
                put_call_volume_ratio_average_over_n_days,
            )

        # Calcluating PC Change from Yesterday
        if len(sorted_dates_set) > 1:
            yesterday_date = sorted_dates_set[1]
            put_call_vol_ratio_yesterday = map_date_to_put_call_volume_ratio[
                yesterday_date
            ]

            if put_call_volume_ratio_current_day and put_call_vol_ratio_yesterday:
                absolute_pc_change_since_yesterday = (
                    put_call_volume_ratio_current_day - put_call_vol_ratio_yesterday
                )
            else:
                absolute_pc_change_since_yesterday = None
        else:
            absolute_pc_change_since_yesterday = None
        if StrategyVariables.flag_test_print:
            print(
                f"Absolute PC Change since yesterday",
                absolute_pc_change_since_yesterday,
            )

        # Check for early termination
        if Utils.flag_check_early_termination_of_indicator(
            indicator_id=indicator_id, instrument_id=instrument_id
        ):
            return

        values_dict = {
            "put_call_volume_ratio_current_day": (
                round(put_call_volume_ratio_current_day, 2)
                if put_call_volume_ratio_current_day
                else put_call_volume_ratio_current_day
            ),
            "put_call_volume_ratio_average_over_n_days": (
                round(put_call_volume_ratio_average_over_n_days, 2)
                if put_call_volume_ratio_average_over_n_days
                else put_call_volume_ratio_average_over_n_days
            ),
            "absolute_pc_change_since_yesterday": (
                round(absolute_pc_change_since_yesterday, 2)
                if absolute_pc_change_since_yesterday
                else absolute_pc_change_since_yesterday
            ),
        }

        # Update value in DB, Object & GUI
        IndicatorHelper.update_indicator_values_for_indcator_id(
            indicator_id=indicator_object.indicator_id, values_dict=values_dict
        )
