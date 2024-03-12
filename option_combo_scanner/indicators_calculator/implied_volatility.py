import asyncio
import copy
import datetime
import math
import pprint
import time
import traceback

import numpy as np
import pandas as pd
from tabulate import tabulate

from com.contracts import get_contract
from com.variables import variables
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.indicators_calculator.helper_binary_search_for_delta_iv import \
    BinarySearchDeltaIV
from option_combo_scanner.indicators_calculator.helper_indicator import \
    IndicatorHelper
from option_combo_scanner.indicators_calculator.historical_data_fetcher import \
    HistoricalDataFetcher
from option_combo_scanner.indicators_calculator.market_data_fetcher import \
    MarketDataFetcher
from option_combo_scanner.strategy.strategy_variables import StrategyVariables
from option_combo_scanner.strategy.utilities import StrategyUtils


class ImpliedVolatility:
    scanner_indicator_tab_iv_obj = None

    def __init__(self):
        pass

    @staticmethod
    def annalize_value(value):
        # TODO  - Achin
        annualized_value = value * math.sqrt(variables.minutes_in_year / variables.hv_mins_in_candle)
        return annualized_value

    @staticmethod
    def calculate_risk_reversal_for_target_delta(df_call, df_put, iv_column_name: str, delta_column_name: str, target_delta: float):
        """
        Calculate risk reversal based on the nearest call and put deltas to the target delta.
        """
        nearest_call_index = (df_call[delta_column_name] - target_delta).abs().idxmin()
        nearest_put_index = (df_put[delta_column_name] - target_delta).abs().idxmin()

        # Get the full row of data for the nearest call and put options
        nearest_call_data = df_call.loc[nearest_call_index]
        nearest_put_data = df_put.loc[nearest_put_index]

        # Calculate risk reversal based on the nearest call and put deltas to the target delta.
        risk_reversal = nearest_call_data[iv_column_name] - nearest_put_data[iv_column_name]

        return risk_reversal

    @staticmethod
    def calculate_iv_for_target_delta(df_call, df_put, iv_column_name: str, delta_column_name: str, target_delta: float):
        """
        Calculate implied volatility based on the nearest call and put deltas to the target delta.
        """

        # Find the nearest call and put deltas to the target delta
        nearest_call_index = (df_call[delta_column_name] - target_delta).abs().idxmin()
        nearest_put_index = (df_put[delta_column_name] - target_delta).abs().idxmin()

        # Retrieve the nearest call and put data
        nearest_call_data = df_call.loc[nearest_call_index]
        nearest_put_data = df_put.loc[nearest_put_index]

        implied_volatility = (nearest_call_data[iv_column_name] + nearest_put_data[iv_column_name]) / 2

        return implied_volatility

    @staticmethod
    def calculate_min_max_pain_strikes(df_call, df_put, indicator_id=None):
        """
        Calculate Min And Max Pain
        """
        # Selecting desired columns from each dataframe
        call_option_subset = df_call[["Strike", "CallOI"]]
        put_option_subset = df_put[["Strike", "PutOI"]]

        # Merging the two dataframes on the "Strike" column
        merged_df = pd.merge(call_option_subset, put_option_subset, on="Strike", how="outer")

        # If you want to fill NaN values with 0
        merged_df.fillna(0, inplace=True)
        merged_df = merged_df.sort_values(by="Strike", ascending=True)  # TODO 

        # Assume market expires at each strike price
        merged_df["Loss Value of Calls"] = 0
        merged_df["Loss Value of Puts"] = 0
        

        # """
        # AT 7800, Base Strike
        #     Call Loss Money when Base Strike > Current Stirke: Loss is Strike Diff * CurrentStirkeCallOI
        # """

        # # Calculate call losses using vectorized operations
        # for strike in merged_df["Strike"]:
        #     strike_diff = strike - merged_df["Strike"]
        #     merged_df["Loss Value of Calls"] += merged_df["CallOI"] * (strike_diff > 0)

        # """
        # AT 7700, Base Strike
        #     Put Loss Money when Current Stirke > Base Strike: Loss is Strike Diff * CurrentStirkePutOI
        # """
        # # Calculate put losses using vectorized operations
        # for strike in merged_df["Strike"]:
        #     strike_diff = merged_df["Strike"] - strike
        #     merged_df["Loss Value of Puts"] += merged_df["PutOI"] * (strike_diff > 0)

        list_of_strike = merged_df["Strike"]
        list_of_call_oi = merged_df["CallOI"]
        list_of_put_oi = merged_df["PutOI"]

        # Calculate call losses
        for indx, strike in enumerate(list_of_strike):
            call_loss_value_at_strike = 0
            put_loss_value_at_strike = 0

            for _strike, _call_oi, _put_oi in zip(list_of_strike, list_of_call_oi, list_of_put_oi):
                strike_diff = abs(_strike - strike)
                call_loss_value_at_strike += 0 if strike < _strike else (_call_oi * strike_diff)
                put_loss_value_at_strike += 0 if strike >= _strike else (_put_oi * strike_diff)

            merged_df.at[indx, "Loss Value of Calls"] = call_loss_value_at_strike
            merged_df.at[indx, "Loss Value of Puts"] = put_loss_value_at_strike

        # Calculate total loss for each strike
        merged_df["Total Loss Value"] = merged_df["Loss Value of Calls"] + merged_df["Loss Value of Puts"]

        # If flag is True store CSV Files
        if StrategyVariables.flag_store_csv_files:
            folder_name = "MinMaxPain"
            file_name = fr"{indicator_id}_MinMaxPain"
            StrategyUtils.save_option_combo_scanner_csv_file(merged_df, folder_name, file_name)

        min_loss_index = merged_df["Total Loss Value"].idxmin()
        max_loss_index = merged_df["Total Loss Value"].idxmax()
        
        # get the strike with max/min total values
        max_pain_strike = merged_df.loc[min_loss_index, "Strike"]
        min_pain_strike = merged_df.loc[max_loss_index, "Strike"]
        
        return max_pain_strike, min_pain_strike

    @staticmethod
    def calculate_oi_support_resistance_strikes(df_call, df_put, current_underlying_price, indicator_id):
        """
        Calculate Min And Max Pain
        """
        # df_call = Such that the strike is greater than or equal to current_underlying_price
        # df_put = Such that the strike is lower than equal to current_underlying_price

        df_call = df_call[df_call['Strike'] >= current_underlying_price]
        df_put = df_put[df_put['Strike'] <= current_underlying_price]

        resistance_index = df_call["CallOI"].idxmax()
        support_index = df_put["PutOI"].idxmax()

        # get the strike with max/min total values
        resistance_strike = df_call.loc[resistance_index, "Strike"]
        support_strike = df_put.loc[support_index, "Strike"]

        # If flag is True store CSV Files
        if StrategyVariables.flag_store_csv_files:
            folder_name = "OpenInterest"
            file_name = fr"{indicator_id}_Call_OI"
            StrategyUtils.save_option_combo_scanner_csv_file(df_call, folder_name, file_name)
            
            file_name = fr"{indicator_id}_Put_OI"
            StrategyUtils.save_option_combo_scanner_csv_file(df_put, folder_name, file_name)

        return support_strike, resistance_strike

    @staticmethod
    def calcluate_current_price(df, delta_column_name: str, target_delta: float):
        """
        Calculate implied volatility based on the nearest call and put deltas to the target delta.
        """
        if df.empty:
            return None
        # Find the nearest index such that the deltas closest to the target delta
        nearest_index = (df[delta_column_name] - target_delta).abs().idxmin()

        # Retrieve the nearest call and put data
        df_data = df.loc[nearest_index]

        current_mkt_price = (df_data["Bid"] + df_data["Ask"]) / 2

        return current_mkt_price

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
    ):
        """
        # Current: IVD1, IVD2, AvgIV,
        # Current: RRD1, RRD2,

        # Current: Max & Min Pain
        # Current: OI Support(Put) and OI Resistance(Call)
        # AvgIV-Avg(14),
        # RR(Chg-14D), RR(Chg-1D),
        # AvgIV(Chg-1D),

        #  Change Options Price Today:   1D Old: (Strike, Delta, IV)
        # CurrentPrice - OldPrice
            # Call/Put  DeltaD1 DeltaD2:   Calculate for 4 Options Contract: 4 Historical data
        # Change Underlying / Change Options Price Today    <Call/Put>(Strike:D1 Strike:D2)
        # Change Underlying / Change Options Price 14DayAgo <Call/Put>(Strike:D1 Strike:D2)
        # AvgIV is need for HV (minus) IV
        # AvgIV(Chg-1D) <I.V. Change> is required for PC-Change/AvgIV(Chg-1D)

        """
        # Indicator ID
        indicator_id = indicator_object.indicator_id

        # Get the current date
        current_date_for_dte = datetime.datetime.today().strftime("%Y%m%d")
        current_date_obj_for_dte = datetime.datetime.strptime(current_date_for_dte, "%Y%m%d")
        expiry_date_obj_for_dte = datetime.datetime.strptime(expiry, "%Y%m%d")

        dte = abs(current_date_obj_for_dte - expiry_date_obj_for_dte).days

        # print(f"Underlying Con: {underlying_contract}")
        # Get Underlying Price
        underlying_bid, underlying_ask = asyncio.run(MarketDataFetcher.get_current_price_for_contract(underlying_contract))

        # Price is not available
        if underlying_bid is None or underlying_ask is None:
            # Can not compute the values
            print(
                f"Inside implied volatiltiy compute unable to get underlying_bid: {underlying_bid}, underlying_ask: {underlying_ask} for Indicator Object:\n{indicator_object}"
            )
            return None, None

        # Current underlying price
        current_underlying_price = (underlying_bid + underlying_ask) / 2

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

        generic_tick_list = "101"  # "101, 100"
        snapshot = False

        # Getting the DataFrames with Mkt data colums = [Strike, Delta, ConId, Bid, Ask]
        (
            call_option_mkt_data_df,
            put_option_mkt_data_df,
        ) = IndicatorHelper.get_mkt_data_df_for_call_and_put_options(
            list_of_all_call_option_contracts, list_of_all_put_option_contracts, snapshot=snapshot, generic_tick_list=generic_tick_list
        )
        # Print to console
        if variables.flag_debug_mode:
            print(f"\nCall ")
            print(
                tabulate(
                    call_option_mkt_data_df.head(5),
                    headers="keys",
                    tablefmt="psql",
                    showindex=False,
                )
            )

            print(f"\nPut ")
            print(tabulate(put_option_mkt_data_df.head(5), headers="keys", tablefmt="psql", showindex=False))

        # If flag is True store CSV Files
        if StrategyVariables.flag_store_csv_files:
            folder_name = "CurrentMktData"
            file_name = fr"{indicator_id}_Call"
            StrategyUtils.save_option_combo_scanner_csv_file(call_option_mkt_data_df, folder_name, file_name)

            file_name = fr"{indicator_id}_Put"
            StrategyUtils.save_option_combo_scanner_csv_file(put_option_mkt_data_df, folder_name, file_name)

        delta_d1 = StrategyVariables.delta_d1_indicator_input
        delta_d2 = StrategyVariables.delta_d2_indicator_input

        # Target Deltas
        list_of_target_deltas = [StrategyVariables.delta_d1_indicator_input, StrategyVariables.delta_d2_indicator_input]
        iv_column_name = "AskIV"
        delta_column_name = "Delta"

        # Copy both the df_call, df_put
        df_call = call_option_mkt_data_df.copy()
        df_put = put_option_mkt_data_df.copy()

        df_call.dropna(subset=[iv_column_name, delta_column_name], inplace=True)
        df_put.dropna(subset=[iv_column_name, delta_column_name], inplace=True)

        # Make delta abs
        df_put["Delta"] = df_put["Delta"].abs()

        if df_call.empty or df_put.empty:
            # Calculating current iv values for D1 and D2
            current_iv_d1 = None
            current_iv_d2 = None

            # Calculating current RR values for D1 and D2
            current_rr_d1 = None
            current_rr_d2 = None
        else:
            # Calculating current iv values for D1 and D2
            current_iv_d1 = ImpliedVolatility.calculate_iv_for_target_delta(df_call, df_put, iv_column_name, delta_column_name, delta_d1)
            current_iv_d2 = ImpliedVolatility.calculate_iv_for_target_delta(df_call, df_put, iv_column_name, delta_column_name, delta_d2)

            # Calculating current RR values for D1 and D2
            current_rr_d1 = ImpliedVolatility.calculate_risk_reversal_for_target_delta(
                df_call, df_put, iv_column_name, delta_column_name, delta_d1
            )
            current_rr_d2 = ImpliedVolatility.calculate_risk_reversal_for_target_delta(
                df_call, df_put, iv_column_name, delta_column_name, delta_d2
            )
            


        df_call = call_option_mkt_data_df.copy()
        df_put = put_option_mkt_data_df.copy()

        if df_call.empty or df_put.empty:
            max_pain_strike, min_pain_strike = None, None
        else:
            max_pain_strike, min_pain_strike = ImpliedVolatility.calculate_min_max_pain_strikes(df_call, df_put, indicator_id)

        df_call.dropna(subset=["CallOI", "PutOI",], inplace=True)
        df_put.dropna(subset=["CallOI", "PutOI", ], inplace=True)

        # Make delta abs
        # df_put["Delta"] = df_put["Delta"].abs()

        if df_call.empty or df_put.empty:
            support_strike, resistance_strike = None, None
        else:
            support_strike, resistance_strike = ImpliedVolatility.calculate_oi_support_resistance_strikes(df_call, df_put, current_underlying_price, indicator_id, )

        current_avg_iv = (current_iv_d1 + current_iv_d2) / 2 if current_iv_d1 and current_iv_d2 else None
        print(f"Indicaor ID: {indicator_object.indicator_id}")
        print(f"{current_iv_d1=},  {current_iv_d2=} , {current_rr_d1=}, {current_rr_d2=}, {max_pain_strike=}, {min_pain_strike=} , {support_strike=}, {resistance_strike=}, {current_avg_iv=}")

        # Map
        map_ith_day_to_ith_day_avg_iv = {}
        map_ith_day_to_ith_day_avg_iv[f"0D-AvgIV"] = current_avg_iv if current_avg_iv else 0

        # [(1D, 0.25)] = IV for 1D delta 0.25
        map_ith_day_and_target_delta_d_to_call_iv_value = {}  # key: (day, targetdelta) = iv
        map_ith_day_and_target_delta_d_to_put_iv_value = {}

        map_ith_day_and_target_delta_d_to_call_strike = {}  # key: (day, targetdelta) = iv
        map_ith_day_and_target_delta_d_to_put_strike = {}

        n_th_day = StrategyVariables.avg_iv_lookback_days

        # We want to compute 1D-AvgIV to 13D-AvgIV
        for right in ["Call", "Put"]:
            if right == "Call":
                dataframe_with_current_mkt_data = df_call.copy()
            elif right == "Put":
                dataframe_with_current_mkt_data = df_put.copy()

            current_date = datetime.datetime.today().strftime("%Y%m%d")
            current_date_obj = datetime.datetime.strptime(current_date, "%Y%m%d")

            expiry_date_obj = datetime.datetime.strptime(expiry, "%Y%m%d")
            time_to_expiration = abs(current_date_obj - expiry_date_obj).days

            for ith_day in range(1, n_th_day):

                # Current Remaining time to expiration + ith_day  (ith_day=1, calculate yesterday iv)
                time_to_expiration = (time_to_expiration + ith_day) / 365

                # Get the strike along with delta & iv value, such that the target delta is nearest
                # For getting these values we can compute the IV_D1 and IV_D2 and AvgIV for ith_day
                # [Tar.DeltaD1: (Strike, Delta, IV,), Tar.DeltaD2: (Strike, Delta, IV,)]
                list_of_strike_delta_iv_tuple = BinarySearchDeltaIV.find_the_strike_delta_iv_tuple(
                    current_underlying_price,
                    right,
                    time_to_expiration,
                    dataframe_with_current_mkt_data,  # Righ C / P only
                    list_of_target_deltas,
                )

                for target_delta, (strikeee, _, iv_at_target_delta) in zip(list_of_target_deltas, list_of_strike_delta_iv_tuple):
                    if right == "Call":
                        map_ith_day_and_target_delta_d_to_call_iv_value[(ith_day, target_delta)] = iv_at_target_delta
                        map_ith_day_and_target_delta_d_to_call_strike[(ith_day, target_delta)] = float(strikeee)
                    else:
                        map_ith_day_and_target_delta_d_to_put_iv_value[(ith_day, target_delta)] = iv_at_target_delta
                        map_ith_day_and_target_delta_d_to_put_strike[(ith_day, target_delta)] = float(strikeee)

        # TODO Comment
        for ith_day in range(1, n_th_day):
            map_ith_day_to_ith_day_avg_iv[f"{ith_day}D-AvgIV"] = (
                map_ith_day_and_target_delta_d_to_call_iv_value[(ith_day, delta_d1)]
                + map_ith_day_and_target_delta_d_to_call_iv_value[(ith_day, delta_d2)]
                + map_ith_day_and_target_delta_d_to_put_iv_value[(ith_day, delta_d1)]
                + map_ith_day_and_target_delta_d_to_put_iv_value[(ith_day, delta_d2)]
            ) / 4

        avg_iv_over_n_days = sum(map_ith_day_to_ith_day_avg_iv.values()) / len(map_ith_day_to_ith_day_avg_iv)

        # Calcualte AbsoluteChange & PercentageChange Since Yesterday
        yesterday_avg_iv = map_ith_day_to_ith_day_avg_iv[f"1D-AvgIV"]
        if yesterday_avg_iv and current_avg_iv:
            absolute_change_in_avg_iv_since_yesterday = current_avg_iv - yesterday_avg_iv
            percentage_change_in_avg_iv_since_yesterday = ((current_avg_iv - yesterday_avg_iv) / yesterday_avg_iv) * 100
        else:
            absolute_change_in_avg_iv_since_yesterday = None
            percentage_change_in_avg_iv_since_yesterday = None

        # DeltaD1, DeltaD2:  RR(Chg-1D), RR(Chg-14D), ,
        # Getting Call & Put IV for Yesterday and LastDay at DeltaD1 and DeltaD2
        n_th_day = n_th_day - 1  # the oldest day for which we are calculating the IV and Delta
        yesterday_delta_d1_call_iv = map_ith_day_and_target_delta_d_to_call_iv_value[(1, delta_d1)]
        yesterday_delta_d2_call_iv = map_ith_day_and_target_delta_d_to_call_iv_value[(1, delta_d2)]
        yesterday_delta_d1_put_iv = map_ith_day_and_target_delta_d_to_put_iv_value[(1, delta_d1)]
        yesterday_delta_d2_put_iv = map_ith_day_and_target_delta_d_to_put_iv_value[(1, delta_d2)]
        n_th_day_delta_d1_call_iv = map_ith_day_and_target_delta_d_to_call_iv_value[(n_th_day, delta_d1)]
        n_th_day_delta_d2_call_iv = map_ith_day_and_target_delta_d_to_call_iv_value[(n_th_day, delta_d2)]
        n_th_day_delta_d1_put_iv = map_ith_day_and_target_delta_d_to_put_iv_value[(n_th_day, delta_d1)]
        n_th_day_delta_d2_put_iv = map_ith_day_and_target_delta_d_to_put_iv_value[(n_th_day, delta_d2)]

        # Calculating the RR for Yesterday & LastDay at DeltaD1 and DeltaD2
        yesterday_delta_d1_risk_reveral = yesterday_delta_d1_call_iv - yesterday_delta_d1_put_iv
        yesterday_delta_d2_risk_reveral = yesterday_delta_d2_call_iv - yesterday_delta_d2_put_iv
        n_th_day_delta_d1_risk_reveral = n_th_day_delta_d1_call_iv - n_th_day_delta_d1_put_iv
        n_th_day_delta_d2_risk_reveral = n_th_day_delta_d2_call_iv - n_th_day_delta_d2_put_iv
        
        print(f"Indicaor ID: {indicator_object.indicator_id}")
        # Calculating the PercentangeInRR since Yesterday & LastDay at DeltaD1 and DeltaD2
        if current_rr_d1 and yesterday_delta_d1_risk_reveral:
            percentage_change_in_rr_since_yesterday_d1 = (
                (current_rr_d1 - yesterday_delta_d1_risk_reveral) / yesterday_delta_d1_risk_reveral
            ) * 100
            print(f"Current RR D1: {current_rr_d1}, Yesterday RR D1: {yesterday_delta_d1_risk_reveral}, Percentage Change: {percentage_change_in_rr_since_yesterday_d1}")
        else:
            percentage_change_in_rr_since_yesterday_d1 = None

        if current_rr_d2 and yesterday_delta_d2_risk_reveral:
            percentage_change_in_rr_since_yesterday_d2 = (
                (current_rr_d2 - yesterday_delta_d2_risk_reveral) / yesterday_delta_d2_risk_reveral
            ) * 100
            print(f"Current RR D2: {current_rr_d2}, Yesterday RR D2: {yesterday_delta_d2_risk_reveral}, Percentage Change: {percentage_change_in_rr_since_yesterday_d2}")
        else:
            percentage_change_in_rr_since_yesterday_d2 = None

        if current_rr_d1 and n_th_day_delta_d1_risk_reveral:
            percentage_change_in_rr_since_14_day_d1 = (
                (current_rr_d1 - n_th_day_delta_d1_risk_reveral) / n_th_day_delta_d1_risk_reveral
            ) * 100
            print(f"Current RR D1: {current_rr_d1}, 14 Day Ago RR D1: {n_th_day_delta_d1_risk_reveral}, Percentage Change: {percentage_change_in_rr_since_14_day_d1}")
        else:
            percentage_change_in_rr_since_14_day_d1 = None

        if current_rr_d2 and n_th_day_delta_d2_risk_reveral:
            percentage_change_in_rr_since_14_day_d2 = (
                (current_rr_d2 - n_th_day_delta_d2_risk_reveral) / n_th_day_delta_d2_risk_reveral
            ) * 100
            print(f"Current RR D2: {current_rr_d2}, 14 Day Ago RR D2: {n_th_day_delta_d2_risk_reveral}, Percentage Change: {percentage_change_in_rr_since_14_day_d2}")
        else:
            percentage_change_in_rr_since_14_day_d2 = None


        values_dict = {
            "current_iv_d1": round(current_iv_d1 * 100, 2) if current_iv_d1 else current_iv_d1,
            "current_iv_d2": round(current_iv_d2 * 100, 2) if current_iv_d2 else current_iv_d2,
            "current_avg_iv": round(current_avg_iv * 100, 2) if current_avg_iv else current_avg_iv,
            "avg_iv_over_n_days": round(avg_iv_over_n_days * 100, 2) if avg_iv_over_n_days else avg_iv_over_n_days,
            "absolute_change_in_avg_iv_since_yesterday": round(absolute_change_in_avg_iv_since_yesterday * 100, 2) if absolute_change_in_avg_iv_since_yesterday else absolute_change_in_avg_iv_since_yesterday,
            "percentage_change_in_avg_iv_since_yesterday": round(percentage_change_in_avg_iv_since_yesterday, 2) if percentage_change_in_avg_iv_since_yesterday else percentage_change_in_avg_iv_since_yesterday,
            "current_rr_d1": round(current_rr_d1 * 100, 2) if current_rr_d1 else current_rr_d1,
            "current_rr_d2": round(current_rr_d2 * 100, 2) if current_rr_d2 else current_rr_d2,
            "percentage_change_in_rr_since_14_day_d1": round(percentage_change_in_rr_since_14_day_d1, 2) if percentage_change_in_rr_since_14_day_d1 else percentage_change_in_rr_since_14_day_d1,
            "percentage_change_in_rr_since_14_day_d2": round(percentage_change_in_rr_since_14_day_d2, 2) if percentage_change_in_rr_since_14_day_d2 else percentage_change_in_rr_since_14_day_d2,
            "percentage_change_in_rr_since_yesterday_d1": round(percentage_change_in_rr_since_yesterday_d1, 2) if percentage_change_in_rr_since_yesterday_d1 else percentage_change_in_rr_since_yesterday_d1,
            "percentage_change_in_rr_since_yesterday_d2": round(percentage_change_in_rr_since_yesterday_d2, 2) if percentage_change_in_rr_since_yesterday_d2 else percentage_change_in_rr_since_yesterday_d2,
            "max_pain_strike": round(max_pain_strike, 2) if max_pain_strike else max_pain_strike,
            "min_pain_strike": round(min_pain_strike, 2) if min_pain_strike else min_pain_strike,
            "oi_support_strike": round(support_strike, 2) if support_strike else support_strike,
            "oi_resistance_strike": round(resistance_strike, 2) if resistance_strike else resistance_strike,
        }

        # Update value in DB, Object & GUI 
        IndicatorHelper.update_indicator_values_for_indcator_id(indicator_id=indicator_object.indicator_id, values_dict=values_dict)

        print("Map (ith Day, Target Delta) to Put Strike:")
        pprint.pprint(map_ith_day_and_target_delta_d_to_put_strike)
        
        print("Map (ith Day, Target Delta) to Call Strike:")
        pprint.pprint(map_ith_day_and_target_delta_d_to_call_strike)

        # Copy both the df_call, df_put
        df_call = call_option_mkt_data_df.copy()
        df_put = put_option_mkt_data_df.copy()

        df_call.dropna(subset=["Bid", "Ask", delta_column_name], inplace=True)
        df_put.dropna(subset=["Bid", "Ask", delta_column_name], inplace=True)

        # Make delta abs
        df_put["Delta"] = df_put["Delta"].abs()

        #  ChangeInOptionPriceSince{Yesterday/NthDay}{DeltaD1/DeltaD2}
        map_var_to_change_in_option_price_value = ImpliedVolatility.compute_change_in_option_price(
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
            df_call,
            df_put,
            map_ith_day_and_target_delta_d_to_call_strike,
            map_ith_day_and_target_delta_d_to_put_strike,
            delta_d1,
            delta_d2,
            n_th_day,
        )

        print("Map Change in option Price")
        pprint.pprint(map_var_to_change_in_option_price_value)

        # Update value in DB, Object & GUI 
        IndicatorHelper.update_indicator_values_for_indcator_id(indicator_id=indicator_object.indicator_id, values_dict=map_var_to_change_in_option_price_value)

        # Flag is off then get the strike and reutrn Values
        if StrategyVariables.flag_put_call_indicator_based_on_selected_deltas_only:
            try:
                # Copy both the df_call, df_put
                df_call = call_option_mkt_data_df.copy()
                df_put = put_option_mkt_data_df.copy()

                delta_column_name = "Delta"
                delta_d1 = abs(delta_d1)
                delta_d2 = abs(delta_d2)

                df_call.dropna(subset=[delta_column_name], inplace=True)
                df_put.dropna(subset=[delta_column_name], inplace=True)
                        
                # Make delta abs
                df_put["Delta"] = df_put["Delta"].abs()

                if df_call.empty or df_put.empty:
                    return None, None
                
                list_of_call_strike, list_of_put_strikes = ImpliedVolatility.get_call_strike_and_put_strike_for_target_delta(df_call, df_put, delta_column_name, delta_d1, delta_d2)
                return list_of_call_strike, list_of_put_strikes
            
            except Exception as e:
                print(f"In ImpliedVolatility.compute() Exception: {e} TraceBack: {traceback.format_exc()}")

        return None, None

    @staticmethod
    def get_call_strike_and_put_strike_for_target_delta(df_call, df_put, delta_column_name: str, target_delta_d1: float, target_delta_d2: float):
        """
        Get the strike for the call and put options for the target delta
        """
        list_of_call_strike = []
        list_of_put_strike = []
        
        for target_delta in [target_delta_d1, target_delta_d2]:
            nearest_call_index = (df_call[delta_column_name] - target_delta).abs().idxmin()
            nearest_put_index = (df_put[delta_column_name] - target_delta).abs().idxmin()

            # Retrieve the nearest call and put data
            nearest_call_data = df_call.loc[nearest_call_index]
            nearest_put_data = df_put.loc[nearest_put_index]

            list_of_call_strike.append(nearest_call_data["Strike"])
            list_of_put_strike.append(nearest_put_data["Strike"])
        
        return list_of_call_strike, list_of_put_strike

    @staticmethod
    def compute_change_in_option_price(
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
        call_option_mkt_data_df,
        put_option_mkt_data_df,
        map_ith_day_and_target_delta_d_to_call_strike,
        map_ith_day_and_target_delta_d_to_put_strike,
        delta_d1,
        delta_d2,
        n_th_day,
    ):
        """
        Computes the change in option price for 4 Contracts (D1, P) (D2, P) (D1, C) (D2, C)
        Change since yesterday close
        Change from 14days(N) Open
        """
        map_var_to_change_in_option_price_value = {}

        yesterday_call_strike_d1 = map_ith_day_and_target_delta_d_to_call_strike[(1, delta_d1)]
        yesterday_call_strike_d2 = map_ith_day_and_target_delta_d_to_call_strike[(1, delta_d2)]
        yesterday_put_strike_d1 = map_ith_day_and_target_delta_d_to_put_strike[(1, delta_d1)]
        yesterday_put_strike_d2 = map_ith_day_and_target_delta_d_to_put_strike[(1, delta_d2)]

        n_th_day_call_strike_d1 = map_ith_day_and_target_delta_d_to_call_strike[(n_th_day, delta_d1)]
        n_th_day_call_strike_d2 = map_ith_day_and_target_delta_d_to_call_strike[(n_th_day, delta_d2)]
        n_th_day_put_strike_d1 = map_ith_day_and_target_delta_d_to_put_strike[(n_th_day, delta_d1)]
        n_th_day_put_strike_d2 = map_ith_day_and_target_delta_d_to_put_strike[(n_th_day, delta_d2)]

        list_of_strikes = [
            yesterday_call_strike_d1,
            yesterday_call_strike_d2,
            yesterday_put_strike_d1,
            yesterday_put_strike_d2,
            n_th_day_call_strike_d1,
            n_th_day_call_strike_d2,
            n_th_day_put_strike_d1,
            n_th_day_put_strike_d2,
        ]

        list_of_contracts = []

        # Comment TODO
        list_of_rights = ["Call", "Call", "Put", "Put"] * 2

        for strike, right in zip(list_of_strikes, list_of_rights):
            contract = get_contract(
                symbol=symbol,
                sec_type=sec_type,
                exchange=exchange,
                currency=currency,
                expiry_date=expiry,
                strike_price=strike,
                right=right,
                multiplier=multiplier,
                trading_class=trading_class,
            )
            list_of_contracts.append(contract)

        list_of_duration_size = [2] * 4 + [n_th_day] * 4
        what_to_show = "Bid"
        list_of_duration_size_for_fetcher = [f"{_} D" for _ in list_of_duration_size]

        # Put it in the Variable # ARYAN TODO
        bar_size = StrategyVariables.bar_size_for_option_change_cal
        list_of_req_id_for_historical_data = HistoricalDataFetcher.fetch_historical_data_for_list_of_contracts(
            list_of_contracts, bar_size, list_of_duration_size_for_fetcher, what_to_show
        )
        # Historical Data for N-Days now we can need to create daily candles
        for indx, (req_id, duration, contract) in enumerate(zip(list_of_req_id_for_historical_data, list_of_duration_size, list_of_contracts)):
            chng_opt_price = None

            df = variables.map_req_id_to_historical_data_dataframe[req_id]

            if contract.right == "Call":
                current_df = call_option_mkt_data_df.copy()
            else:
                current_df = put_option_mkt_data_df.copy()

            if indx % 2 == 0:
                target_delta_ith = delta_d1
                t_delta = "_d1"
            else:
                target_delta_ith = delta_d2
                t_delta = "_d2"

            if duration == 2:
                day_ = "_yesterday"
            else:
                day_ = "_nth_day"

            if current_df.empty or df.empty:
                pass
            else:
                # If True Save the CSV File
                if StrategyVariables.flag_store_csv_files:
                    folder_name = "ChangeInOptionPrice"
                    file_name = fr"{indicator_object.indicator_id}_{contract.right}_{day_}_{t_delta}_{contract.strike}"
                    StrategyUtils.save_option_combo_scanner_csv_file(df, folder_name, file_name)

                old_close_price = df.iloc[0]["Close"]

                current_price = ImpliedVolatility.calcluate_current_price(
                    current_df, delta_column_name="Delta", target_delta=target_delta_ith
                )

                if StrategyVariables.flag_chng_in_opt_price_in_percentage:
                    if current_price and old_close_price and old_close_price != 0:
                        chng_opt_price = ((current_price - old_close_price) / old_close_price) * 100
                    else: 
                        chng_opt_price = None
                else:
                    if current_price and old_close_price:
                        chng_opt_price = (current_price - old_close_price)
                    else:
                        chng_opt_price = None
                    print(f"chg_in_{contract.right}_opt_price_since{day_}{t_delta}", f"{current_price=}  {old_close_price=} {chng_opt_price=}")
            
            var_name = f"chg_in_{contract.right}_opt_price_since{day_}{t_delta}".lower()
            map_var_to_change_in_option_price_value[var_name] = round(chng_opt_price, 2) if chng_opt_price else chng_opt_price
        
        return map_var_to_change_in_option_price_value
