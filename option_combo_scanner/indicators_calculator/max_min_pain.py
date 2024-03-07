import asyncio
import copy
import datetime
import time

import numpy as np
import pandas as pd
from tabulate import tabulate

from com import variables
from com.contracts import get_contract
from com.option_comobo_scanner_idetif import (
    find_closest_expiry_for_fop_given_fut_expiries_and_trading_class,
    find_nearest_expiry_and_all_strikes_for_stk_given_dte,
    find_nearest_expiry_for_future_given_fut_dte,
)
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


class Max_Min_Pain:
    scanner_indicator_tab_pain_obj = None

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

        # # only call once (not for N-DTEs)
        # all_fut_expiries = find_nearest_expiry_for_future_given_fut_dte(
        #     symbol,
        #     dte,
        #     underlying_sec_type,
        #     exchange,
        #     currency,
        #     multiplier,
        #     trading_class="",
        #     only_want_all_expiries=True,
        # )

        # # Handling None
        # if all_fut_expiries == None:
        #     return None, None, None

        # print("IV: trying to get underlying")
        # # get closest FOP Expiry for given Trading class
        # (
        #     all_strikes,
        #     closest_expiry_date,
        # ) = find_closest_expiry_for_fop_given_fut_expiries_and_trading_class(
        #     symbol,
        #     dte,
        #     underlying_sec_type,
        #     exchange,
        #     currency,
        #     multiplier,
        #     trading_class,
        #     all_fut_expiries,
        # )

        # print(
        #     "IV: VAL",
        #     all_strikes,
        #     closest_expiry_date,
        #     underlying_conid,
        # )
        # return (all_strikes, closest_expiry_date, underlying_conid)

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

        # Local local_map_indicator_id_to_indicator_object
        local_map_indicator_id_to_indicator_object = copy.deepcopy(
            StrategyVariables.map_indicator_id_to_indicator_object
        )
        # All the indicator rows are unique data needs to be fethced for all, can not reduce the requests call

        for (
            indicator_id,
            indicator_object,
        ) in local_map_indicator_id_to_indicator_object.items():

            # if the indictor was removed, do not compute the values for this
            if (
                indicator_id
                not in StrategyVariables.map_indicator_id_to_indicator_object
            ):
                continue

            instrument_id = indicator_object.instrument_id

            # if the instrument was removed, do not compute the values for this
            if (
                instrument_id
                not in StrategyVariables.map_instrument_id_to_instrument_object
            ):
                continue

            local_instrument_obj = copy.deepcopy(
                StrategyVariables.map_instrument_id_to_instrument_object[instrument_id]
            )

            symbol = indicator_object.symbol
            expiry = indicator_object.expiry
            sec_type = local_instrument_obj.sec_type
            underlying_sec_type = "STK" if sec_type == "OPT" else "FUT"
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
            current_date_for_dte = datetime.datetime.today().strftime("%Y%m%d")
            current_date_obj_for_dte = datetime.datetime.strptime(
                current_date_for_dte, "%Y%m%d"
            )
            expiry_date_obj_for_dte = datetime.datetime.strptime(expiry, "%Y%m%d")

            dte = abs(current_date_obj_for_dte - expiry_date_obj_for_dte).days

            if underlying_sec_type == "FUT":
                (
                    all_strikes,
                    closest_expiry_date,
                    underlying_conid,
                ) = Max_Min_Pain.get_strike_and_closet_expiry_for_fop(
                    indicator_object.symbol,
                    dte,
                    underlying_sec_type,
                    exchange,
                    currency,
                    int(multiplier),
                    trading_class,
                )

                underlying_contract = get_contract(
                    symbol=symbol,
                    sec_type=underlying_sec_type,
                    exchange=exchange,
                    currency=currency,
                    multiplier=multiplier,
                    con_id=underlying_conid,
                )

            elif underlying_sec_type == "STK":
                (
                    all_strikes,
                    closest_expiry_date,
                ) = Max_Min_Pain.get_strike_and_closet_expiry_for_opt(
                    symbol,
                    dte,
                    underlying_sec_type,
                    exchange,
                    currency,
                    multiplier,
                    trading_class,
                )
                # print(all_strikes)
                underlying_contract = get_contract(
                    symbol=symbol,
                    sec_type=underlying_sec_type,
                    exchange=exchange,
                    currency=currency,
                    multiplier=1,
                )
            else:
                continue

            list_of_rights = ["CALL", "PUT"]

            # Get Market Data for all the option contarcts
            for right in list_of_rights:

                list_of_all_option_contracts = []

                for strike in all_strikes:

                    list_of_all_option_contracts.append(
                        get_contract(
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
                    )

                generic_tick_list = "101"  # "101, 100"
                snapshot = False
                # Fetch Data for all the Contracts
                list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple = asyncio.run(
                    MarketDataFetcher.get_option_delta_and_implied_volatility_for_contracts_list_async(
                        list_of_all_option_contracts,
                        True,
                        generic_tick_list=generic_tick_list,
                        snapshot=snapshot,
                    )
                )

                data = []

                # get the strike, call oi and put oi for each contract

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
                    list_of_all_option_contracts,
                    list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple,
                ):
                    # print("calloi and put_oi", call_oi, put_oi)

                    data.append(
                        {
                            "Strike": float(contract.strike),
                            "call_oi": call_oi,
                            "put_oi": put_oi,
                        }
                    )

                df = pd.DataFrame(data)
                df.dropna(inplace=True)

                # print('saved')

                # if right.upper() == 'CALL':
                #     df_call = pd.DataFrame(data)
                #     df_call.dropna(inplace=True)

                # elif right.upper() == 'PUT':
                #     df_put = pd.DataFrame(data)
                #     df_put.dropna(inplace=True)

            # Calculate the max/min pain

            # Calcluate the Cummaltive Call and Put values
            df = Max_Min_Pain.calculate_max_pain(df)

            min_loss_index = df["Total Values"].idxmin()
            max_loss_index = df["Total Values"].idxmax()

            # get the strike with max/min total values
            max_pain = df.loc[min_loss_index, "Strike"]
            min_pain = df.loc[max_loss_index, "Strike"]

            print("Max Pain Strike:", max_pain)
            print("Min Pain Strike:", min_pain)
            Max_Min_Pain.update_values_in_db_gui(min_pain, max_pain, indicator_id)

    @staticmethod
    def calculate_max_pain(strike_oi_df):
        days = len(strike_oi_df)

        # print(days)
        call_loss = [0] * days
        put_loss = [0] * days
        total_loss = [0] * days
        strike_oi_df = strike_oi_df.reset_index(drop=True)
        # Calculate call losses
        for i in range(1, days):
            call_loss[i] = sum(
                strike_oi_df["call_oi"][j]
                * (strike_oi_df["Strike"][i] - strike_oi_df["Strike"][j])
                for j in range(i)
            )

        # Calculate put losses
        for i in range(days - 2, -1, -1):
            put_loss[i] = sum(
                strike_oi_df["put_oi"][j]
                * (strike_oi_df["Strike"][j] - strike_oi_df["Strike"][i])
                for j in range(days - 1, i, -1)
            )

        # Calculate total losses
        for i in range(days):
            total_loss[i] = call_loss[i] + put_loss[i]
        # print(call_loss)
        # Add cumulative columns to DataFrame
        strike_oi_df["Loss value of calls"] = call_loss
        strike_oi_df["Loss value of Put"] = put_loss
        strike_oi_df["Total Values"] = total_loss

        return strike_oi_df

        # subset_df_put.to_csv(fr'Temp\{right}_{symbol}_{StrategyVariables.riskfree_rate1}.csv')

    @staticmethod
    def update_values_in_db_gui(min_pain, max_pain, indicator_id):

        values_dict = {
            "min_pain": min_pain,
            "max_pain": max_pain,
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
            print(f"Pain values not updated in DB", {indicator_id})
            # return

        if indicator_id in StrategyVariables.map_indicator_id_to_indicator_object:
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].min_pain = min_pain
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].max_pain = max_pain

            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "min_pain",
            ] = min_pain

            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "max_pain",
            ] = max_pain

        else:
            print(f"Indicator object not found for indicator_id: {indicator_id}")

        # print(StrategyVariables.scanner_indicator_table_df.to_string())
        Max_Min_Pain.scanner_indicator_tab_pain_obj.update_into_indicator_table(
            StrategyVariables.scanner_indicator_table_df
        )
