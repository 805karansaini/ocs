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
from com.variables import variables
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.greeks import (
    get_underlying_implied_volatility_and_cmp,
)
from option_combo_scanner.indicators_calculator.binary_search_for_delta_iv import (
    BinarySearchDeltaIV,
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


class ImpliedVolatility:
    scanner_indicator_tab_iv_obj = None

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

        # Underlying of Indicators <Contract>
        local_map_indicator_id_to_indicator_object = copy.deepcopy(
            StrategyVariables.map_indicator_id_to_indicator_object
        )
        # All the indicator rows are unique data needs to be fethced for all, can not reduce the requests call

        for (
            indicator_id,
            indicator_object,
        ) in local_map_indicator_id_to_indicator_object.items():

            # if the indictor was removed
            if (
                indicator_id
                not in StrategyVariables.map_indicator_id_to_indicator_object
            ):
                continue

            instrument_id = indicator_object.instrument_id

            # Get all the strikes, so that we can create the FOP OPT contract, for which the below data is required(Strike, Delta, IV )
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
                ) = ImpliedVolatility.get_strike_and_closet_expiry_for_fop(
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
                ) = ImpliedVolatility.get_strike_and_closet_expiry_for_opt(
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
                pass

            # get Underlying Price - S
            bid_ask_price_tuple = asyncio.run(
                MarketDataFetcher.get_current_price_for_contract(underlying_contract)
            )

            if bid_ask_price_tuple[0] and bid_ask_price_tuple[1]:
                current_price = (bid_ask_price_tuple[0] + bid_ask_price_tuple[1]) / 2

            # print(f"Indicator Obj: {indicator_object}, Strikes: {all_strikes}")

            # Get the Strike, Delta, IV for all the calls
            list_of_rights = ["CALL", "PUT"]

            df_put = pd.DataFrame()
            df_call = pd.DataFrame()

            # Get the Strike, Delta, IV for all the puts
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

                flag_market_open = variables.flag_market_open

                # Fetch Data for all the  Contracts
                list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple = asyncio.run(
                    MarketDataFetcher.get_option_delta_and_implied_volatility_for_contracts_list_async(
                        list_of_all_option_contracts,
                        flag_market_open,
                        generic_tick_list=generic_tick_list,
                        snapshot=snapshot,
                    )
                )

                from pprint import pprint

                print(f"Right: {right}")
                pprint(
                    list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple
                )

                data = []
                # TODO -Comment ARYAN take price here (market_premum of the option)
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
                    data.append(
                        {
                            "STRIKE": float(contract.strike),
                            "DELTA": delta,
                            # TODO
                            "IV_ASK": iv_ask if iv_ask else 1,
                            "IV_BID": iv_bid if iv_bid else 1,
                            "IV_LAST": iv_last,
                            "BID": bid_price,
                            "ASK": ask_price,
                            "CALL_OI": call_oi,
                            "PUT_OI": put_oi,
                        }
                    )

                if right.upper() == "CALL":
                    df_call = pd.DataFrame(data)
                    df_call.dropna(inplace=True)

                elif right.upper() == "PUT":
                    df_put = pd.DataFrame(data)
                    df_put.dropna(inplace=True)

            print(f"\nCall ")
            print(tabulate(df_call, headers="keys", tablefmt="psql", showindex=False))

            print(f"\nPut ")
            print(tabulate(df_put, headers="keys", tablefmt="psql", showindex=False))

            delta_d1 = StrategyVariables.delta_d1_indicator_input
            delta_d2 = StrategyVariables.delta_d2_indicator_input
            # Take from user input
            list_of_target_deltas = [delta_d1, delta_d2]

            # Get Current Data CallIV Avg(0.25, 0.5) and PutIV Avg(0.25, 0.5): map_right_day_to_right_iv[(0, right:Call/Put)] = CallIV Avg(0.25, 0.5)
            # IV_D1 and IV_D2
            current_iv_d1 = ImpliedVolatility.get_iv_for_delta(
                df_call, df_put, "IVLAST", "Delta", delta_d1
            )
            # Get IV for respective delta and target delta D2
            current_iv_d2 = ImpliedVolatility.get_iv_for_delta(
                df_call, df_put, "IVLAST", "Delta", delta_d2
            )
            map_day_to_avg_iv = {}

            map_day_to_avg_iv[f"AvgIV_{0}D"] = (current_iv_d1 + current_iv_d2) / 2
            # fun
            map_day_and_target_delta_to_call_iv = {}
            map_day_and_target_delta_to_put_iv = {}  # key: (day, targetdelta) = iv

            for right in list_of_rights:

                if right.upper() == "CALL":
                    dataframe_with_current_mkt_data = df_call.copy()
                elif right.upper() == "PUT":
                    dataframe_with_current_mkt_data = df_put.copy()

                current_date = datetime.datetime.today().strftime("%Y%m%d")
                current_date_obj = datetime.datetime.strptime(current_date, "%Y%m%d")

                expiry_date_obj = datetime.datetime.strptime(expiry, "%Y%m%d")
                time_to_expiration = abs(current_date_obj - expiry_date_obj).days

                for i in range(1, 14):  # TODO TAKE LOOKBACK FROM USER INPUT
                    user_input_date = i

                    time_to_expiration = (time_to_expiration + user_input_date) / 365
                    list_of_strike_delta_iv_tuple = (
                        BinarySearchDeltaIV.find_the_strike_delta_iv_tuple(
                            current_price,
                            right,
                            time_to_expiration,
                            dataframe_with_current_mkt_data,  # Righ C / P only
                            list_of_target_deltas,
                        )
                    )

                    for t_d, (_, _, iv) in zip(
                        list_of_target_deltas, list_of_strike_delta_iv_tuple
                    ):
                        if right.upper() == "CALL":
                            map_day_and_target_delta_to_call_iv[(i, t_d)] = iv
                        else:
                            map_day_and_target_delta_to_put_iv[(i, t_d)] = iv

            total_avg_iv_n_days = 0
            for i in range(0, 14):
                avg_iv_ith_day = (
                    map_day_and_target_delta_to_call_iv[(i, delta_d1)]
                    + map_day_and_target_delta_to_call_iv[(i, delta_d2)]
                    + map_day_and_target_delta_to_put_iv[(i, delta_d1)]
                    + map_day_and_target_delta_to_put_iv[(i, delta_d2)]
                ) / 4

                map_day_to_avg_iv[f"AvgIV_{i}D"] = avg_iv_ith_day
                total_avg_iv_n_days += avg_iv_ith_day

            map_day_to_avg_iv[f"AvgIV-Avg({14}D)"] = total_avg_iv_n_days / 14

            print(map_day_to_avg_iv)
            continue

            if False:
                if False:
                    if all([ask_price, bid_price]):

                        market_premium = (ask_price + bid_price) / 2

                        current_date = datetime.datetime.today().strftime("%Y%m%d")
                        current_date_obj = datetime.datetime.strptime(
                            current_date, "%Y%m%d"
                        )

                        expiry_date_obj = datetime.datetime.strptime(expiry, "%Y%m%d")
                        time_to_expiration = abs(
                            current_date_obj - expiry_date_obj
                        ).days

                        for i in range(15):  # Loop from 14 to 1
                            user_input_date = i

                            time_to_expiration = (
                                time_to_expiration + user_input_date
                            ) / 365

                            # TODO
                            desired_delta, iv = Utils.get_delta(
                                current_price,
                                StrategyVariables.riskfree_rate1,
                                0,
                                time_to_expiration,
                                float(contract.strike),
                                market_premium,
                                right,
                            )

                            data[-1][f"Delta_{i}D"] = desired_delta
                            data[-1][f"IV_{i}D"] = iv
                            data[-1]["market_premium"] = market_premium
                            if i == 0:
                                # print("IV HEre", iv)
                                if delta:
                                    data[-1]["Deltadiff_0D_Current"] = (
                                        desired_delta - delta
                                    )
                                else:
                                    data[-1]["Deltadiff_0D_Current"] = None
                                if iv_last:
                                    # print('IVhere2', iv)
                                    data[-1]["IVdiff_0D_Current"] = iv - iv_last
                                else:
                                    data[-1]["IVdiff_0D_Current"] = None

                    # df = pd.DataFrame(data)
                    # df.dropna(inplace=True)
                    # subset_df = df[['Strike', 'Delta', 'Call_OI']]
                    # subset_df.to_csv(fr'Temp\{right}_{symbol}_{StrategyVariables.riskfree_rate1}.csv')

            # subset_df_call.to_csv(fr'Temp\{right}_{symbol}_{StrategyVariables.riskfree_rate1}.csv')
            # subset_df_put.to_csv(fr'Temp\{right}_{symbol}_{StrategyVariables.riskfree_rate1}.csv')

            df_call.dropna(inplace=True)
            df_put.dropna(inplace=True)

            # print(df_put.to_string())

            # TODO ARYAN:- HV and IV: Positive, Negative  (Check value magnitude)

            # Get all the Avg_IVs It is the Avg of (AvgIV_14D + AvgIV_13D... + CurrentIV)
            avg_ivs = {}
            total_avg_iv = 0
            num_avg_iv = 0

            for i in range(14, 0, -1):
                delta_col = f"Delta_{i}D"
                iv_col = f"IV_{i}D"
                # Get IV for respective delta and target delta D1
                iv_d1 = ImpliedVolatility.get_iv_for_delta(
                    df_call, df_put, iv_col, delta_col, delta_d1
                )
                # Get IV for respective delta and target delta D2
                iv_d2 = ImpliedVolatility.get_iv_for_delta(
                    df_call, df_put, iv_col, delta_col, delta_d2
                )

                if iv_d1 and iv_d2:
                    avg_iv = (iv_d1 + iv_d2) / 2
                    avg_ivs[f"avg_iv_{i}"] = avg_iv
                    total_avg_iv += avg_iv
                    num_avg_iv += 1
                else:
                    avg_iv = None
                    avg_ivs[f"avg_iv_{i}"] = None

            # Calculate the AvgIV-Avg(14D)

            # IV_D1 and IV_D2
            iv_d1 = ImpliedVolatility.get_iv_for_delta(
                df_call, df_put, "IVLAST", "Delta", delta_d1
            )
            # Get IV for respective delta and target delta D2
            iv_d2 = ImpliedVolatility.get_iv_for_delta(
                df_call, df_put, "IVLAST", "Delta", delta_d2
            )

            # AvgIV = Avg(IV(D1),IV(D2))
            if iv_d1 and iv_d2:
                avg_iv = (iv_d1 + iv_d2) / 2
                total_avg_iv += avg_iv
                num_avg_iv += 1
            else:
                avg_iv = None

            if num_avg_iv != 0:
                avg_iv_avg_14d = total_avg_iv / num_avg_iv
            else:
                avg_iv_avg_14d = None

            # Calcluating Change in IV
            iv_d1_yesterday = ImpliedVolatility.get_iv_for_delta(
                df_call, df_put, "IV_1D", "Delta_1D", delta_d1
            )
            iv_d1_current = ImpliedVolatility.get_iv_for_delta(
                df_call, df_put, "IVLAST", "Delta", delta_d1
            )

            if iv_d1_yesterday and iv_d1_current:
                change_in_iv = (
                    (iv_d1_current - iv_d1_yesterday) / iv_d1_yesterday
                ) * 100
            else:
                change_in_iv = None
            print("Changin IV", change_in_iv)

            # if change_in_iv != 0 and pc_change is not None:
            #     pc_change_iv_change = float(pc_change)/change_in_iv
            # else:
            #     pc_change_iv_change = None

            # print("PC Change/IV Change", pc_change_iv_change)
            # def fun()
            # Current Risk Reversal D1
            rr_d1 = ImpliedVolatility.calculate_risk_reversal(df_call, df_put, delta_d1)

            # Current Risk Reversal D2
            rr_d2 = ImpliedVolatility.calculate_risk_reversal(df_call, df_put, delta_d2)

            print("RR D1 and RRD2", rr_d1, rr_d2)

            rr_d1_chg = ImpliedVolatility.calculate_risk_reversal_of_14d_last(
                df_call, df_put, delta_d1
            )
            rr_d2_chg = ImpliedVolatility.calculate_risk_reversal_of_14d_last(
                df_call, df_put, delta_d2
            )

            # TODO: ARYAN HANDLE ERROR
            if rr_d1_chg and rr_d1 and rr_d2_chg and rr_d2 and (rr_d1 and rr_d2 != 0):
                change_rr_d1_14D = ((rr_d1 - rr_d1_chg) / rr_d1_chg) * 100
                change_rr_d2_14D = ((rr_d2 - rr_d2_chg) / rr_d2_chg) * 100
            else:
                change_rr_d1_14D = None
                change_rr_d2_14D = None

            # Calculate RR for ONe day
            rr_d1_1d = ImpliedVolatility.calculate_risk_reversal_of_1d_last(
                df_call, df_put, delta_d1
            )
            rr_d2_1d = ImpliedVolatility.calculate_risk_reversal_of_1d_last(
                df_call, df_put, delta_d2
            )

            # Calculate RR for ONe day Change RR(D1)-Chg(1D)
            if rr_d1_1d and rr_d1 and rr_d2_1d and rr_d2 and (rr_d1 and rr_d2 != 0):
                change_rr_d1_1D = ((rr_d1 - rr_d1_1d) / rr_d1_1d) * 100
                change_rr_d2_1D = ((rr_d2 - rr_d2_1d) / rr_d2_1d) * 100
            else:
                change_rr_d1_1D = None
                change_rr_d2_1D = None

            # Calcluation of OISupport and OIResistance

            if not df_call.empty:
                max_value_idx = df_call["Call_OI"].idxmax()

                open_interest_resistance = df_call.loc[max_value_idx, "Strike"]
            else:
                open_interest_resistance = None

            if not df_put.empty:
                max_put_value_idx = df_put["Put_OI"].idxmax()

                open_interest_support = df_put.loc[max_put_value_idx, "Strike"]
            else:
                open_interest_support = None

            print("OIRes", open_interest_support)
            print("OIRes", open_interest_resistance)

            # print(change_rr_d1_14D, change_rr_d2_14D)

            ImpliedVolatility.update_values_in_db_gui(
                rr_d1,
                rr_d2,
                iv_d1,
                iv_d2,
                avg_iv,
                avg_iv_avg_14d,
                change_rr_d1_1D,
                change_rr_d2_1D,
                change_rr_d1_14D,
                change_rr_d2_14D,
                open_interest_support,
                open_interest_resistance,
                change_in_iv,
                indicator_id,
            )

            return avg_iv

    # Function to calculate Risk Reversal d1 RR(D1)
    @staticmethod
    def update_values_in_db_gui(
        rr_d1,
        rr_d2,
        iv_d1,
        iv_d2,
        avg_iv,
        avg_iv_avg_14d,
        change_rr_d1_1D,
        change_rr_d2_1D,
        change_rr_d1_14D,
        change_rr_d2_14D,
        open_interest_support,
        open_interest_resistance,
        change_in_iv,
        indicator_id,
    ):

        values_dict = {
            "rr_d1": rr_d1,
            "rr_d2": rr_d2,
            "iv_d1": iv_d1,
            "iv_d2": iv_d2,
            "avg_iv": avg_iv,
            "avg_iv_avg_14d": avg_iv_avg_14d,
            "change_rr_d1_1D": change_rr_d1_1D,
            "change_rr_d2_1D": change_rr_d2_1D,
            "change_rr_d1_14D": change_rr_d1_14D,
            "change_rr_d2_14D": change_rr_d2_14D,
            "open_interest_support": open_interest_support,
            "open_interest_resistance": open_interest_resistance,
            "change_in_iv": change_in_iv,
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
            print(f"IV values not updated in DB", {indicator_id})
            # return

        if indicator_id in StrategyVariables.map_indicator_id_to_indicator_object:
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].iv_d1 = iv_d1
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].iv_d2 = iv_d2
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].avg_iv = avg_iv
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].rr_d1 = rr_d1
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].rr_d2 = rr_d2
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].avg_iv_avg_14d = avg_iv_avg_14d
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].change_rr_d1_1D = change_rr_d1_1D
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].change_rr_d2_1D = change_rr_d2_1D
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].change_rr_d1_14D = change_rr_d1_14D
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].change_rr_d2_14D = change_rr_d2_14D
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].open_interest_support = open_interest_support
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].open_interest_resistance = open_interest_resistance
            StrategyVariables.map_indicator_id_to_indicator_object[
                indicator_id
            ].change_in_iv = change_in_iv

            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "iv_d1",
            ] = iv_d1
            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "iv_d2",
            ] = iv_d2
            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "avg_iv",
            ] = avg_iv
            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "rr_d1",
            ] = rr_d1
            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "rr_d2",
            ] = rr_d2
            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "avg_iv_avg_14d",
            ] = avg_iv_avg_14d
            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "change_rr_d1_1D",
            ] = change_rr_d1_1D
            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "change_rr_d2_1D",
            ] = change_rr_d2_1D
            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "change_rr_d1_14D",
            ] = change_rr_d1_14D
            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "change_rr_d2_14D",
            ] = change_rr_d2_14D
            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "open_interest_support",
            ] = open_interest_support
            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "open_interest_resistance",
            ] = (open_interest_resistance,)

            StrategyVariables.scanner_indicator_table_df.loc[
                StrategyVariables.scanner_indicator_table_df["Indicator ID"]
                == indicator_id,
                "change_in_iv",
            ] = (change_in_iv,)

        else:
            print(f"Indicator object not found for indicator_id: {indicator_id}")

        # print(StrategyVariables.scanner_indicator_table_df.to_string())
        ImpliedVolatility.scanner_indicator_tab_iv_obj.update_into_indicator_table(
            StrategyVariables.scanner_indicator_table_df
        )

    @staticmethod
    def calculate_risk_reversal(df_call, df_put, target_delta):
        if df_call.empty or df_put.empty:
            return None

        nearest_call_index = (df_call["Delta"] - target_delta).abs().idxmin()
        nearest_put_index = (df_put["Delta"] - target_delta).abs().idxmin()

        # If nearest_call_index or nearest_put_index is empty, return None
        if np.isnan(nearest_call_index) or np.isnan(nearest_put_index):
            return None

        # Get the full row of data for the nearest call and put options
        nearest_call_data = df_call.loc[nearest_call_index]
        nearest_put_data = df_put.loc[nearest_put_index]

        # Calculate risk reversal

        risk_reversal = nearest_call_data["IVLAST"] - nearest_put_data["IVLAST"]

        # TODO ARYAN:- IV: Positive, Negative  (Check value magnitude)

        return risk_reversal

    @staticmethod
    def get_iv_for_delta(df_call, df_put, iv_col, delta_col, target_delta):
        """
        Calculate implied volatility based on the nearest call and put deltas to the target delta.
        """
        if df_call.empty or df_put.empty:
            return None

        # Find the nearest call and put deltas to the target delta
        nearest_call_index = (df_call[delta_col] - target_delta).abs().idxmin()
        nearest_put_index = (df_put[delta_col] - target_delta).abs().idxmin()

        # If nearest call or put index is not found, return None
        if pd.isnull(nearest_call_index) or pd.isnull(nearest_put_index):
            return None

        # Retrieve the nearest call and put data
        nearest_call_data = df_call.loc[nearest_call_index]
        nearest_put_data = df_put.loc[nearest_put_index]
        if nearest_call_data[iv_col] and nearest_put_data[iv_col]:
            # Calculate implied volatility using specified IV column names
            implied_volatility = (
                nearest_call_data[iv_col] + nearest_put_data[iv_col]
            ) / 2
        else:
            implied_volatility = None
        return implied_volatility

    @staticmethod
    def calculate_risk_reversal_of_14d_last(
        df_call,
        df_put,
        target_delta,
    ):
        """ """
        if df_call.empty or df_put.empty:
            return None

        nearest_call_index = (df_call["Delta_14D"] - target_delta).abs().idxmin()
        nearest_put_index = (df_put["Delta_14D"] - target_delta).abs().idxmin()

        # If nearest_call_index or nearest_put_index is empty, return None
        if np.isnan(nearest_call_index) or np.isnan(nearest_put_index):
            return None

        # Get the full row of data for the nearest call and put options
        nearest_call_data = df_call.loc[nearest_call_index]
        nearest_put_data = df_put.loc[nearest_put_index]

        # Calculate risk reversal
        risk_reversal_chg_14 = nearest_call_data["IV_14D"] - nearest_put_data["IV_14D"]
        return risk_reversal_chg_14

    @staticmethod
    def calculate_risk_reversal_of_1d_last(
        df_call,
        df_put,
        target_delta,
    ):
        if df_call.empty or df_put.empty:
            return None

        nearest_call_index = (df_call["Delta_1D"] - target_delta).abs().idxmin()
        nearest_put_index = (df_put["Delta_1D"] - target_delta).abs().idxmin()

        # If nearest_call_index or nearest_put_index is empty, return None
        if np.isnan(nearest_call_index) or np.isnan(nearest_put_index):
            return None

        # Get the full row of data for the nearest call and put options
        nearest_call_data = df_call.loc[nearest_call_index]
        nearest_put_data = df_put.loc[nearest_put_index]

        # Calculate risk reversal
        risk_reversal_chg_1d = nearest_call_data["IV_1D"] - nearest_put_data["IV_1D"]
        return risk_reversal_chg_1d
