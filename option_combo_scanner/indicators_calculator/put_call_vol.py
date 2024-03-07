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


class PutCallVol:
    scanner_indicator_tab_pc_obj = None

    def __init__(self):
        pass

    @staticmethod
    def get_strike_and_closet_expiry_for_fop(
        symbol,
        dte,
        underlying_sec_type,
        exchange,
        currency,
        multiplier,
        trading_class,
    ):
        """
        Function used to get the
        list of all the available strikes
        and closest expiry for FOP sec_type

        """
        print(
            "IV: trying to get all_exp",
            symbol,
            dte,
            underlying_sec_type,
            exchange,
            currency,
            multiplier,
            trading_class,
        )

        # only call once (not for N-DTEs)
        all_fut_expiries = find_nearest_expiry_for_future_given_fut_dte(
            symbol,
            dte,
            underlying_sec_type,
            exchange,
            currency,
            multiplier,
            trading_class="",
            only_want_all_expiries=True,
        )

        # Handling None
        if all_fut_expiries == None:
            return None, None, None

        # get closest FOP Expiry for given Trading class
        (
            all_strikes,
            closest_expiry_date,
            underlying_conid,
        ) = find_closest_expiry_for_fop_given_fut_expiries_and_trading_class(
            symbol,
            dte,
            underlying_sec_type,
            exchange,
            currency,
            multiplier,
            trading_class,
            all_fut_expiries,
        )

        return all_strikes, closest_expiry_date, underlying_conid

    @staticmethod
    def get_strike_and_closet_expiry_for_opt(
        symbol,
        dte,
        underlying_sec_type,
        exchange,
        currency,
        multiplier,
        trading_class,
    ):
        """
        Function used to get the
        list of all the available strikes
        and closest expiry for OPT sec_type

        """
        (
            all_expiry_dates_ticker,
            all_strikes,
            closest_expiry_date,
            underlying_conid,
        ) = find_nearest_expiry_and_all_strikes_for_stk_given_dte(
            ticker=symbol,
            days_to_expiry=dte,
            underlying_sec_type=underlying_sec_type,
            exchange=exchange,
            currency=currency,
            multiplier=multiplier,
            fop_trading_class="",
        )

        if all_strikes is not None:

            # Removing  {  }
            all_strikes = [float(_) for _ in all_strikes[1:-1].split(",")]

            all_strikes = sorted(all_strikes)

        return all_strikes, closest_expiry_date

    @staticmethod
    def compute():
        """
        Indicator Row:
            m. Put/Call Volume Ratio:
            n. Put/Call Volume Ratio Average:
            u. PC Change only  (PC Change / I.V. Change:
        """

        # Local local_map_indicator_id_to_indicator_object
        local_map_indicator_id_to_indicator_object = copy.deepcopy(
            StrategyVariables.map_indicator_id_to_indicator_object
        )

        # All the indicator rows are unique data needs to be fethced for all, can not reduce the requests call
        for (
            indicator_id,
            indicator_object,
        ) in local_map_indicator_id_to_indicator_object.items():
            """
            Iterate and compute the value for the respective row
            """

            # if the indictor was removed, do not compute the values for this
            if (
                indicator_id
                not in StrategyVariables.map_indicator_id_to_indicator_object
            ):
                continue

            # Intrument ID
            instrument_id = indicator_object.instrument_id

            # if the instrument was removed, do not compute the values for this
            if (
                instrument_id
                not in StrategyVariables.map_instrument_id_to_instrument_object
            ):
                continue

            # Create the local copy of instrument_obj
            local_instrument_obj = copy.deepcopy(
                StrategyVariables.map_instrument_id_to_instrument_object[instrument_id]
            )

            symbol = indicator_object.symbol
            expiry = indicator_object.expiry  # OPT/FOP expiry
            sec_type = local_instrument_obj.sec_type  # OPT/FOP
            exchange = local_instrument_obj.exchange
            currency = local_instrument_obj.currency
            multiplier = local_instrument_obj.multiplier
            trading_class = local_instrument_obj.trading_class

            # Underlying SecType
            if sec_type.strip().upper() == "OPT":
                underlying_sec_type = "STK"
            elif sec_type.strip().upper() == "FOP":
                underlying_sec_type = "FUT"
            else:
                # if the underlying sec_type is not valid continue
                continue

            # Get the current date
            current_date_str = datetime.datetime.today().strftime("%Y%m%d")
            current_date_obj = datetime.datetime.strptime(current_date_str, "%Y%m%d")
            expiry_date_obj = datetime.datetime.strptime(expiry, "%Y%m%d")

            dte = abs(expiry_date_obj - current_date_obj).days

            map_date_to_put_volume = {}
            map_date_to_call_volume = {}

            # Getting the underlying_contarct, and all the call and put option contracts
            (
                underlying_contract,
                list_of_all_call_option_contracts,
                list_of_all_put_option_contracts,
            ) = PutCallVol.get_underlying_and_list_of_call_and_put_option_contracts(
                symbol,
                sec_type,
                expiry,
                dte,
                underlying_sec_type,
                exchange,
                currency,
                multiplier,
                trading_class,
            )

            if (
                underlying_contract is None
                or list_of_all_call_option_contracts is None
                or list_of_all_put_option_contracts is None
            ):
                # TODO KARAN
                continue

            # Get Market Data for underlying contract
            underlying_bid, underlying_ask = asyncio.run(
                MarketDataFetcher.get_current_price_for_contract(underlying_contract)
            )

            if underlying_bid is None or underlying_ask is None:
                # TODO KARAN
                # TODO - ARYAN HANDLE ERRROR - Please give reason/try to understand this part
                current_underlying_price = None
            else:
                current_underlying_price = (underlying_ask + underlying_bid) / 2

            # Getting the DataFrames with Mkt data colums = [Strike, Delta, ConId, Bid, Ask]
            (
                call_option_mkt_data_df,
                put_option_mkt_data_df,
            ) = PutCallVol.get_mkt_data_df_for_call_and_put_options(
                list_of_all_call_option_contracts, list_of_all_put_option_contracts
            )

            if StrategyVariables.flag_indication_values_based_on_selected_deltas:
                """
                Option 2: Use volume data specific to delta strikes.

                <Sticky Delta>
                1. Contract: Get the option contract such that the delta is nearest to target delta
                2. 1D Volume: Request Historical Trades Data for all the contracts
                3. Compute P/C Ratio today
                4. Avg P/C over N-days for specific delta
                5. P/C Change one day
                """
                pass

            else:
                """
                Option 1: Volume data for all the option strikes.
                ND, N-1D.. 1D Volume: Request Historical Trades Data for all the contracts

                """
                # WE WANT HISTORICAL DATA what_to_show = TRADES
                # bar_size = StrategyVariables.bar_size_pc_vol_avg
                # duration_size = StrategyVariables.lookback_days_pc_vol_avg
                what_to_show = "TRADES"

                call_list_of_daily_volume_data_df = []
                put_list_of_daily_volume_data_df = []

                # Fetch Historical data
                for right, list_option_contracts in [
                    ("CALL", list_of_all_call_option_contracts),
                    ("PUT", list_of_all_put_option_contracts),
                ]:
                    middle_index = len(list_option_contracts) // 2

                    # TODO REMOVE THIS TEST CODE
                    middle_5_contracts = list_option_contracts[
                        middle_index - 2 : middle_index + 3
                    ]
                    # bar_size = "4 hours"
                    # duration_size = "2 D"

                    list_of_req_ids_for_volume = PutCallVol.fetch_historical_data(
                        middle_5_contracts,
                        StrategyVariables.bar_size_pc_vol_avg,
                        StrategyVariables.lookback_days_pc_vol_avg,
                        what_to_show,
                    )

                    # Historical Data for N-Days now we can need to create daily candles
                    for req_id in list_of_req_ids_for_volume:
                        df = variables.map_req_id_to_historical_data_dataframe[req_id]

                        daily_data_df = PutCallVol.create_daily_candle_df_from_raw_df(
                            df
                        )

                        if right == "CALL":
                            call_list_of_daily_volume_data_df.append(daily_data_df)
                        elif right == "PUT":
                            put_list_of_daily_volume_data_df.append(daily_data_df)

                # Map to store total volume for Call and Put
                total_put_volume = {}
                total_call_volume = {}
                put_call_volume_ratio = {}

                # Get the Sorted Date Set
                combined_list_of_daily_volume_data_df = (
                    call_list_of_daily_volume_data_df + put_list_of_daily_volume_data_df
                )

                # print(combined_list_of_daily_volume_data_df)
                all_dates = pd.concat(
                    [
                        df["date"]
                        for df in combined_list_of_daily_volume_data_df
                        if not df.empty
                    ]
                )

                # Drop duplicates and sort the dates in reverse order
                sorted_dates = sorted(all_dates.drop_duplicates(), reverse=True)

                # Convert sorted_dates to a set
                sorted_dates_set = sorted(list(set(sorted_dates)), reverse=True)

                latest_date = sorted_dates_set[0]
                # print(latest_date)

                for date in sorted_dates_set:
                    # get the total volume for Call and Put
                    (
                        total_call_vol_for_date,
                        total_put_vol_for_date,
                    ) = PutCallVol.get_total_vol_for_date(
                        date,
                        call_list_of_daily_volume_data_df,
                        put_list_of_daily_volume_data_df,
                    )
                    total_put_volume[date] = total_put_vol_for_date
                    total_call_volume[date] = total_call_vol_for_date

                    # Calculate the put-call volume ratio
                    if total_call_vol_for_date != 0:
                        put_call_volum_ratio = (
                            total_put_vol_for_date / total_call_vol_for_date
                        )
                    else:
                        put_call_volum_ratio = None  # Handle division by zero case

                    # Store the put-call volume ratio for the date
                    put_call_volume_ratio[date] = put_call_volum_ratio

            # Make Sure length of dict >= 2  sorted_dates_set
            put_call_volume_ratio_current = put_call_volume_ratio[latest_date]
            # print(put_call_volume_ratio)
            non_none_pc_values = filter(
                lambda x: x is not None, put_call_volume_ratio.values()
            )
            if sum(total_call_volume.values()) != 0:
                pc_ratio_avg = sum(non_none_pc_values) / len(put_call_volume_ratio)
            else:
                pc_ratio_avg = None

            print(f"current pc ratio today", put_call_volume_ratio_current)
            print(f"pc ratio avg", pc_ratio_avg)

            # Calcluating PC Change from Yesterday
            if len(sorted_dates_set) > 1:
                yesterday_date = sorted_dates_set[1]
                put_call_vol_ratio_yesterday = put_call_volume_ratio[yesterday_date]

                if put_call_volume_ratio_current and put_call_vol_ratio_yesterday:
                    pc_change = (
                        put_call_volume_ratio_current - put_call_vol_ratio_yesterday
                    )
                else:
                    pc_change = None
            else:
                pc_change = None

            print(f"PC Change", pc_change)
            PutCallVol.update_values_in_db_gui(
                indicator_id, pc_change, pc_ratio_avg, put_call_volume_ratio_current
            )

            """
                for req_id, contract in zip(list_of_req_ids_for_volume, middle_5_contracts):

                    df = variables.map_req_id_to_historical_data_dataframe[req_id]

                    if df is not None:
                        # Convert 'date' column to datetime if it's not already in datetime format
                        df["Time"] = pd.to_datetime(df["Time"])

                        # Extract unique dates and initialize lists to store aggregated values
                        unique_dates = df["Time"].dt.date.unique()
                        open_values = []
                        close_values = []
                        vol_values = []

                        # Iterate over unique dates and aggregate 'open' and 'close' values
                        for date in unique_dates:
                            date_df = df[df["Time"].dt.date == date]
                            open_sum = date_df["Open"].sum()
                            close_sum = date_df["Close"].sum()
                            vol_sum = date_df["Volume"].sum()
                            open_values.append(open_sum)
                            close_values.append(close_sum)
                            vol_values.append(vol_sum)

                        # Create a new DataFrame with aggregated values for each date
                        df_daily_sum = pd.DataFrame(
                            {
                                "date": unique_dates,
                                "open": open_values,
                                "close": close_values,
                                "volume": vol_values,
                            }
                        )
                    else:
                        print(f"DataFrame is empty")

                    # TODO  df_daily_sum = S1 daily historical volume data
                    for date, volume in zip(df_daily_sum["date"], df_daily_sum["volume"]):
                        if right == "PUT":
                            map_date_to_put_volume[date] = map_date_to_put_volume.get(date, 0) + volume
                        elif right == "CALL":
                            map_date_to_call_volume[date] = map_date_to_call_volume.get(date, 0) + volume

            # print(map_date_to_call_volume)
            # print(map_date_to_put_volume)

                        market_premium = (ask_price + bid_price) / 2

                        current_date = datetime.datetime.today().strftime("%Y%m%d")
                        current_date_obj = datetime.datetime.strptime(current_date, "%Y%m%d")

                        expiry_date_obj = datetime.datetime.strptime(expiry, "%Y%m%d")
                        time_to_expiration = (abs(expiry_date_obj - current_date_obj).days + 14) / 365

                        # getting the delta for the strike from black scholes
                        black_scholes_delta, black_scholes_iv = Utils.get_delta(
                            current_price_today,
                            StrategyVariables.riskfree_rate1,
                            0,
                            time_to_expiration,
                            float(contract.strike),
                            market_premium,
                            right,
                        )

                        # storing the delta and strike for all the option contract
                        data_for_all_contract_to_get_nearest_strike[-1]["Delta"] = black_scholes_delta

                # print(f"list of all delta strike", data_for_all_contract_to_get_nearest_strike)
                target_deltas = [0.5, 0.25]

                # Initialize variables to store the closest strikes
                closest_strikes_14d = {target_delta: None for target_delta in target_deltas}

                # Iterate through the data and find strikes nearest to the desired deltas
                for item in data_for_all_contract_to_get_nearest_strike:
                    strike = item["Strike"]
                    delta = item["Delta"]

                    if delta is not None:
                        for target_delta in target_deltas:
                            # If closest strike is not set or if current strike is closer to target delta
                            if closest_strikes_14d[target_delta] is None or abs(delta - target_delta) < abs(
                                closest_strikes_14d[target_delta] - target_delta
                            ):
                                closest_strikes_14d[target_delta] = strike
                    else:
                        pass
                        # print(f"Delta not available for strike {strike}. Skipping...")
                # Print the strikes nearest to desired deltas
            print(closest_strikes_14d)
            unique_strikes = set(closest_strikes_14d.values())

            filtered_closest_strikes_14d = list(unique_strikes)
            # list_of_rights = ["CALL", "PUT"]

            # Create Option Contract for the filtered strikes (Black Scholes Model) and get the historical data
            for right in list_of_rights:
                list_of_filtered_option_contracts = []
                # print(filtered_closest_strikes)
                for filtered_strike in filtered_closest_strikes_14d:

                    list_of_filtered_option_contracts.append(
                        get_contract(
                            symbol=symbol,
                            sec_type=sec_type,
                            multiplier=multiplier,
                            exchange=exchange,
                            currency=currency,
                            right=right,
                            strike_price=filtered_strike,
                            expiry_date=expiry,
                            trading_class=trading_class,
                        )
                    )

                # Fetch the Historical Data
                middle_index = len(list_of_filtered_option_contracts) // 2

                middle_5_contracts = list_of_filtered_option_contracts[middle_index - 2 : middle_index + 3]
                # print(middle_5_contracts)
                list_of_req_ids_for_volume = PutCallVol.fetch_historical_data(middle_5_contracts)

                for req_id, contract in zip(list_of_req_ids_for_volume, middle_5_contracts):

                    df = variables.map_req_id_to_historical_data_dataframe[req_id]
                    # print(contract)
                    df.to_csv(f"Temp/{contract.symbol}_{contract.right}.csv")

                    if df is not None:
                        # Convert 'date' column to datetime if it's not already in datetime format
                        df["Time"] = pd.to_datetime(df["Time"])

                        # Extract unique dates and initialize lists to store aggregated values
                        unique_dates = df["Time"].dt.date.unique()
                        open_values = []
                        close_values = []
                        vol_values = []

                        # Iterate over unique dates and aggregate 'open' and 'close' values
                        for date in unique_dates:
                            date_df = df[df["Time"].dt.date == date]
                            open_sum = date_df["Open"].sum()
                            close_sum = date_df["Close"].sum()
                            vol_sum = date_df["Volume"].sum()
                            open_values.append(open_sum)
                            close_values.append(close_sum)
                            vol_values.append(vol_sum)

                        # Create a new DataFrame with aggregated values for each date
                        df_daily_sum = pd.DataFrame(
                            {
                                "date": unique_dates,
                                "open": open_values,
                                "close": close_values,
                                "volume": vol_values,
                            }
                        )
                    else:
                        print(f"DataFrame is empty")

                    # TODO  df_daily_sum = S1 daily historical volume data
                    for date, volume in zip(df_daily_sum["date"], df_daily_sum["volume"]):
                        if right == "PUT":
                            map_date_to_put_volume_delta_based[date] = map_date_to_put_volume_delta_based.get(date, 0) + volume
                        elif right == "CALL":
                            map_date_to_call_volume_delta_based[date] = map_date_to_call_volume_delta_based.get(date, 0) + volume

            # print(map_date_to_call_volume_delta_based)
            # print(map_date_to_put_volume_delta_based)

            delta_based_dateset = sorted(
                set(list(map_date_to_call_volume_delta_based.keys()) + list(map_date_to_put_volume_delta_based.keys()))
            )
            # print(delta_based_dateset)

            # Loop over sorted dates to calculate put/call volume ratio
            if delta_based_dateset:
                for date in delta_based_dateset:
                    put_volume_delta_based = map_date_to_put_volume_delta_based.get(date, 0)
                    call_volume_delta_based = map_date_to_call_volume_delta_based.get(date, 0)

                    if call_volume_delta_based != 0:
                        put_call_ratio = put_volume_delta_based / call_volume_delta_based
                        # print(f"{date}: {put_call_ratio}")
                    else:
                        put_call_ratio = None

                put_call_ratio_current_option_2 = put_call_ratio
            else:
                put_call_ratio_current_option_2 = None

            if sum(map_date_to_call_volume_delta_based.values()) != 0:
                put_call_ratio_avg_option_2 = sum(map_date_to_put_volume_delta_based.values()) / sum(
                    map_date_to_call_volume_delta_based.values()
                )
            else:
                put_call_ratio_avg_option_2 = None

            print(f"PCVol Avg Option 2 {put_call_ratio_avg_option_2}_{contract.symbol}")
            print("PC VOl Ratio Current Option 2", put_call_ratio_current_option_2)

            dates_set = sorted(set(list(map_date_to_put_volume.keys()) + list(map_date_to_call_volume.keys())))
            # print(dates_set)

            # Loop over sorted dates to calculate put/call volume ratio
            for date in dates_set:
                put_volume = map_date_to_put_volume.get(date, 0)
                call_volume = map_date_to_call_volume.get(date, 0)

                if call_volume != 0:
                    put_call_ratio = put_volume / call_volume
                    # print(f"{date}: {put_call_ratio}")
                else:
                    put_call_ratio = None
            put_call_ratio_current = put_call_ratio
            if sum(map_date_to_call_volume.values()) != 0:
                put_call_ratio_avg = sum(map_date_to_put_volume.values()) / sum(map_date_to_call_volume.values())
            else:
                put_call_ratio_avg = None
            print(f"PC Vol Avg Option 1 {put_call_ratio_avg}_{contract.symbol}")
            print("Pc Vol Current Option 1", put_call_ratio_current)

            # Calcluating pc change
            current_date = dates_set[-1]
            yesterday_date = dates_set[-2]

            # Calcluating PC Today
            put_volume_current = map_date_to_put_volume.get(current_date, 0)
            call_volume_current = map_date_to_call_volume.get(current_date, 0)

            if call_volume_current != 0:
                put_call_ratio_current = put_volume_current / call_volume_current
            else:
                put_call_ratio_current = None

            # Calcluating PC Yesterday
            put_volume_yesterday = map_date_to_put_volume.get(yesterday_date, 0)
            call_volume_yesterday = map_date_to_call_volume.get(yesterday_date, 0)

            if call_volume_yesterday != 0:
                put_call_ratio_yesterday = put_volume_yesterday / call_volume_yesterday
            else:
                put_call_ratio_yesterday = None

            if put_call_ratio_current and put_call_ratio_yesterday:
                pc_change = put_call_ratio_current - put_call_ratio_yesterday
            else:
                pc_change = None

            # print('PC Change', pc_change)
            # print(f"PC Vol Avg Option 1 {put_call_ratio_avg}_{contract.symbol}")
            # print('Pc Vol Current Option 1', put_call_ratio_current)

            PutCallVol.update_values_in_db_gui(indicator_id, pc_change, put_call_ratio_avg, put_call_ratio_current)
            
            return pc_change
            """

    @staticmethod
    def fetch_historical_data(
        list_of_all_option_contracts, bar_size, duration_size, what_to_show
    ):

        # List of all request ids TODO
        list_of_req_id_for_historical_data = []

        for contract in list_of_all_option_contracts:

            # Getting req_id
            reqId = variables.cas_app.nextorderId
            variables.cas_app.nextorderId += 1

            # Send the request
            HistoricalDataFetcher.request_historical_data_for_contract(
                contract, bar_size, duration_size, what_to_show, reqId
            )

            # Append the reqId to list
            list_of_req_id_for_historical_data.append(reqId)

        counter = 0
        while variables.cas_wait_time_for_historical_data > (
            counter * variables.sleep_time_between_iters
        ):

            # Waitting for the request to end or give error
            if all(
                [
                    variables.req_mkt_data_end[req_id] or variables.req_error[req_id]
                    for req_id in list_of_req_id_for_historical_data
                ]
            ):
                break

            # Sleep for sleep_time_waiting_for_tws_response
            time.sleep(variables.sleep_time_between_iters)

            # Increase Counter
            counter += 1

        return list_of_req_id_for_historical_data

    @staticmethod
    def update_values_in_db_gui(
        indicator_id, pc_change, put_call_ratio_avg, put_call_ratio_current
    ):

        values_dict = {
            "pc_change": pc_change,
            "put_call_ratio_avg": put_call_ratio_avg,
            "put_call_ratio_current": put_call_ratio_current,
        }

        where_condition = f" WHERE `indicator_id` = {indicator_id};"

        select_query = SqlQueries.create_update_query(
            table_name="indicator_table",
            values_dict=values_dict,
            where_clause=where_condition,
        )
        # Get all the old rows from indicator table
        res = SqlQueries.execute_update_query(select_query)

        if not res:
            print(f"PC values not updated in DB", {indicator_id})
            # return

        if indicator_id in StrategyVariables.map_indicator_id_to_indicator_object:
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].pc_change = pc_change
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].put_call_ratio_avg = put_call_ratio_avg
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].put_call_ratio_current = put_call_ratio_current

            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "pc_change",
            ] = pc_change
            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "put_call_ratio_avg",
            ] = put_call_ratio_avg
            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "put_call_ratio_current",
            ] = put_call_ratio_current

        else:
            print(f"Indicator object not found for indicator_id: {indicator_id}")

        PutCallVol.scanner_indicator_tab_pc_obj.update_into_indicator_table(
            StrategyVariables.scanner_indicator_table_df
        )

    @staticmethod
    def get_underlying_and_list_of_call_and_put_option_contracts(
        symbol,
        sec_type,
        expiry,
        dte,
        underlying_sec_type,
        exchange,
        currency,
        multiplier,
        trading_class,
    ):
        # Get all the strikes, so that we can create the FOP OPT contract, for which the below data is required(Strike, Delta, IV )
        if underlying_sec_type == "FUT":

            # Get all the strike for the FOP and underlying FUT conid
            (
                all_strikes,
                closest_expiry_date,
                underlying_conid,
            ) = PutCallVol.get_strike_and_closet_expiry_for_fop(
                symbol,
                dte,
                underlying_sec_type,
                exchange,
                currency,
                int(multiplier),
                trading_class,
            )

            # Underlying FUT contract needed for underlying market price, which is required in black scholes
            underlying_contract = get_contract(
                symbol=symbol,
                sec_type=underlying_sec_type,
                exchange=exchange,
                currency=currency,
                multiplier=multiplier,
                con_id=underlying_conid,
            )

        elif underlying_sec_type == "STK":
            # Get all the strike for the OPT
            (
                all_strikes,
                closest_expiry_date,
            ) = PutCallVol.get_strike_and_closet_expiry_for_opt(
                symbol,
                dte,
                underlying_sec_type,
                exchange,
                currency,
                multiplier,
                trading_class,
            )

            # Underlying STK contract needed for underlying market price, which is required in black scholes
            underlying_contract = get_contract(
                symbol=symbol,
                sec_type=underlying_sec_type,
                exchange=exchange,
                currency=currency,
                multiplier=1,
            )
        else:
            # if the underlying sec_type is not valid continue
            return None, None, None

        # print(f"Indicator Obj: {indicator_object}, Strikes: {all_strikes}")

        # Init list
        list_of_all_call_option_contracts = []
        list_of_all_put_option_contracts = []

        # Get the Strike, Delta, IV for all the calls
        list_of_rights = ["CALL", "PUT"]

        # Get the Strike, Delta, IV for all the Option Contracts on both Call and Put sides
        for right in list_of_rights:

            # Creating and appending the option contracts to the above list
            for strike in all_strikes:
                opt_contract = get_contract(
                    symbol=symbol,
                    sec_type=sec_type,
                    multiplier=multiplier,
                    exchange=exchange,
                    currency=currency,
                    right=right,
                    strike_price=strike,
                    expiry_date=expiry,
                    trading_class=trading_class,
                )

                if right == "CALL":
                    list_of_all_call_option_contracts.append(opt_contract)
                else:
                    list_of_all_put_option_contracts.append(opt_contract)

        return (
            underlying_contract,
            list_of_all_call_option_contracts,
            list_of_all_put_option_contracts,
        )

    @staticmethod
    def get_mkt_data_df_for_call_and_put_options(
        list_of_all_call_option_contracts, list_of_all_put_option_contracts
    ):
        generic_tick_list = ""
        snapshot = False

        # Option MKT Data DFs, PUT MKT Data DFs
        columns = [
            "Strike",
            "Delta",
            "ConId",
            "Bid",
            "Ask",
        ]

        # CALL: Fetch Data for all the  Contracts will only use bid ask for market premium
        call_list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple = asyncio.run(
            MarketDataFetcher.get_option_delta_and_implied_volatility_for_contracts_list_async(
                list_of_all_call_option_contracts,
                True,
                generic_tick_list=generic_tick_list,
                snapshot=snapshot,
            )
        )

        call_option_data_frame_dict = {col: [] for col in columns}

        for contract, (
            delta,
            iv_ask,
            iv_bid,
            iv_last,
            bid_price,
            ask_price,
            call_oi,
            put_oi,
        ) in zip(
            list_of_all_call_option_contracts,
            call_list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple,
        ):
            call_option_data_frame_dict["Strike"].append(contract.strike)
            call_option_data_frame_dict["Delta"].append(str(delta))
            call_option_data_frame_dict["ConId"].append(contract.conId)
            call_option_data_frame_dict["Bid"].append(bid_price)
            call_option_data_frame_dict["Ask"].append(ask_price)

        call_option_mkt_data_df = pd.DataFrame(call_option_data_frame_dict)

        # PUT: Fetch Data for all the  Contracts will only use bid ask for market premium
        put_list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple = asyncio.run(
            MarketDataFetcher.get_option_delta_and_implied_volatility_for_contracts_list_async(
                list_of_all_put_option_contracts,
                True,
                generic_tick_list=generic_tick_list,
                snapshot=snapshot,
            )
        )

        put_option_data_frame_dict = {col: [] for col in columns}

        for contract, (
            delta,
            iv_ask,
            iv_bid,
            iv_last,
            bid_price,
            ask_price,
            call_oi,
            put_oi,
        ) in zip(
            list_of_all_put_option_contracts,
            call_list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple,
        ):
            put_option_data_frame_dict["Strike"].append(contract.strike)
            put_option_data_frame_dict["Delta"].append(str(delta))
            put_option_data_frame_dict["ConId"].append(contract.conId)
            put_option_data_frame_dict["Bid"].append(bid_price)
            put_option_data_frame_dict["Ask"].append(ask_price)

        put_option_mkt_data_df = pd.DataFrame(put_option_data_frame_dict)

        return call_option_mkt_data_df, put_option_mkt_data_df

    @staticmethod
    def create_daily_candle_df_from_raw_df(df):
        df_daily_sum = pd.DataFrame()
        if not df.empty:
            # Convert 'date' column to datetime if it's not already in datetime format
            df["Time"] = pd.to_datetime(df["Time"])

            # Extract unique dates and initialize lists to store aggregated values
            unique_dates = df["Time"].dt.date.unique()
            open_values = []
            close_values = []
            vol_values = []

            # Iterate over unique dates and aggregate 'open' and 'close' values
            for date in unique_dates:
                date_df = df[df["Time"].dt.date == date]
                open_sum = date_df["Open"].sum()
                close_sum = date_df["Close"].sum()
                vol_sum = date_df["Volume"].sum()
                open_values.append(open_sum)
                close_values.append(close_sum)
                vol_values.append(vol_sum)

            # Create a new DataFrame with aggregated values for each date
            df_daily_sum = pd.DataFrame(
                {
                    "date": unique_dates,
                    "open": open_values,
                    "close": close_values,
                    "volume": vol_values,
                }
            )
        else:
            print(f"DataFrame is empty")

        return df_daily_sum

    @staticmethod
    def get_total_vol_for_date(
        date, call_list_of_daily_volume_data_df, put_list_of_daily_volume_data_df
    ):
        total_call_vol_for_date = 0
        total_put_vol_for_date = 0

        # Iterate through call_list_of_daily_volume_data_df and put_list_of_daily_volume_data_df to find volumes for the given date
        for df in call_list_of_daily_volume_data_df:

            # get vol for date
            if not df.empty:
                vol_for_date = df[df["date"] == date]["volume"].sum()
                total_call_vol_for_date += float(vol_for_date)

        for df in put_list_of_daily_volume_data_df:
            if not df.empty:
                vol_for_date = df[df["date"] == date]["volume"].sum()
                total_put_vol_for_date += float(vol_for_date)

        return total_call_vol_for_date, total_put_vol_for_date
