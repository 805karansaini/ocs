import asyncio
import copy
import datetime
import pprint
import time

import numpy as np
import pandas as pd
from tabulate import tabulate

# from com import variables
from com.variables import variables
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
from option_combo_scanner.indicators_calculator.put_call_vol import PutCallVol
from option_combo_scanner.strategy.strategy_variables import StrategyVariables


class ChangeinIV:
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
    def compute(pc_change):

        # Map indicator id to indicator object
        local_map_indicator_id_to_indicator_object = copy.deepcopy(
            StrategyVariables.map_indicator_id_to_indicator_object
        )

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

            # If instrument not present continue
            if (
                instrument_id
                not in StrategyVariables.map_instrument_id_to_instrument_object
            ):
                continue

            local_instrument_obj = copy.deepcopy(
                StrategyVariables.map_instrument_id_to_instrument_object[instrument_id]
            )

            # get the indicator_object data
            symbol = indicator_object.symbol
            expiry = indicator_object.expiry
            sec_type = local_instrument_obj.sec_type
            underlying_sec_type = "STK" if sec_type == "OPT" else "FUT"
            exchange = local_instrument_obj.exchange
            currency = local_instrument_obj.currency
            multiplier = local_instrument_obj.multiplier
            trading_class = local_instrument_obj.trading_class

            # Get the current date for calcluating dte
            current_date_for_dte = datetime.datetime.today().strftime("%Y%m%d")
            current_date_obj_for_dte = datetime.datetime.strptime(
                current_date_for_dte, "%Y%m%d"
            )
            expiry_date_obj_for_dte = datetime.datetime.strptime(expiry, "%Y%m%d")

            dte = abs(current_date_obj_for_dte - expiry_date_obj_for_dte).days

            # Get the all strikes and closest expiry for the sec_type
            if underlying_sec_type == "FUT":
                (
                    all_strikes,
                    closest_expiry_date,
                    underlying_conid,
                ) = ChangeinIV.get_strike_and_closet_expiry_for_fop(
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
                ) = ChangeinIV.get_strike_and_closet_expiry_for_opt(
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

            # Calcluate the current price for today
            bid_ask_price_tuple = asyncio.run(
                MarketDataFetcher.get_current_price_for_contract(underlying_contract)
            )

            if bid_ask_price_tuple[0] and bid_ask_price_tuple[1]:
                current_price_today = (
                    bid_ask_price_tuple[0] + bid_ask_price_tuple[1]
                ) / 2
            else:
                # TODO - ARYAN HANDLE ERRROR - Please give reason/try to understand this part
                current_price_today = None

            df_put = pd.DataFrame()
            df_call = pd.DataFrame()

            list_of_rights = ["CALL", "PUT"]
            # Modified new sir code
            # Flow to ge the filtered strike based on D1 and D2 and use black scholes to get strike
            for right in list_of_rights:

                list_of_all_option_contracts = []

                for strike in all_strikes:
                    # Here we are creating list of all option contract
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

                generic_tick_list = ""
                snapshot = False

                # Fetch Data for all the  Contracts will only use bid ask for market prem.

                list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple = asyncio.run(
                    MarketDataFetcher.get_option_delta_and_implied_volatility_for_contracts_list_async(
                        list_of_all_option_contracts,
                        True,
                        generic_tick_list=generic_tick_list,
                        snapshot=snapshot,
                    )
                )

                data_for_all_contract_to_get_nearest_strike = []
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

                    data_for_all_contract_to_get_nearest_strike.append(
                        {
                            "Strike": float(contract.strike),
                            "Delta": None,
                            "IV": None,
                            "IVLAST": iv_last,
                        }
                    )

                    # print(data_for_all_contract_to_get_nearest_strike)
                    if all([ask_price, bid_price]):

                        market_premium = (ask_price + bid_price) / 2

                        current_date = datetime.datetime.today().strftime("%Y%m%d")
                        current_date_obj = datetime.datetime.strptime(
                            current_date, "%Y%m%d"
                        )

                        expiry_date_obj = datetime.datetime.strptime(expiry, "%Y%m%d")
                        time_to_expiration = (
                            abs(expiry_date_obj - current_date_obj).days + 1
                        ) / 365

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
                        data_for_all_contract_to_get_nearest_strike[-1][
                            "Delta"
                        ] = black_scholes_delta
                        data_for_all_contract_to_get_nearest_strike[-1][
                            "IV"
                        ] = black_scholes_iv

                if right.upper() == "CALL":
                    df_call = pd.DataFrame(data_for_all_contract_to_get_nearest_strike)
                    df_call.dropna(inplace=True)

                elif right.upper() == "PUT":
                    df_put = pd.DataFrame(data_for_all_contract_to_get_nearest_strike)
                    df_put.dropna(inplace=True)
                df_call.dropna(inplace=True)
                df_put.dropna(inplace=True)

                delta_d1 = StrategyVariables.delta_d1_indicator_input

                iv_d1_yesterday = ChangeinIV.get_iv_for_delta(
                    df_call, df_put, "IV", "Delta", delta_d1
                )
                iv_d1_current = ChangeinIV.get_iv_for_delta(
                    df_call, df_put, "IVLAST", "Delta", delta_d1
                )

                if iv_d1_yesterday and iv_d1_current:
                    change_in_iv = (
                        (iv_d1_current - iv_d1_yesterday) / iv_d1_yesterday
                    ) * 100
                else:
                    change_in_iv = None
                print("chgiv", change_in_iv)

        # if change_in_iv != 0 and pc_change is not None:
        #     pc_change_iv_change = pc_change/change_in_iv
        # else:
        #     pc_change_iv_change = None

        # print("pcchngeivchge", pc_change_iv_change)

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
