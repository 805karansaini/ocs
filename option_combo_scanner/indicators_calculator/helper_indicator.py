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
    find_nearest_expiry_for_future_given_fut_dte)
from com.variables import variables
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.gui.utils import Utils as GUIUtils
from option_combo_scanner.indicators_calculator.market_data_fetcher import \
    MarketDataFetcher
from option_combo_scanner.strategy.strategy_variables import StrategyVariables


class IndicatorHelper:

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

        # print(
        #     "IV: trying to get all_exp",
        #     symbol,
        #     dte,
        #     underlying_sec_type,
        #     exchange,
        #     currency,
        #     multiplier,
        #     trading_class,
        # )

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
    def get_underlying_contract_and_all_strikes(
        indicator_object, symbol, expiry, sec_type, underlying_sec_type, exchange, currency, multiplier, trading_class
    ):
        underlying_contract, all_strikes = None, None

        try:
            # Get the current date
            current_date_for_dte = datetime.datetime.today().strftime("%Y%m%d")
            current_date_obj_for_dte = datetime.datetime.strptime(current_date_for_dte, "%Y%m%d")
            expiry_date_obj_for_dte = datetime.datetime.strptime(expiry, "%Y%m%d")

            dte = abs(current_date_obj_for_dte - expiry_date_obj_for_dte).days

            if underlying_sec_type == "FUT":
                (
                    all_strikes,
                    closest_expiry_date,
                    underlying_conid,
                ) = IndicatorHelper.get_strike_and_closet_expiry_for_fop(
                    symbol,
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
                ) = IndicatorHelper.get_strike_and_closet_expiry_for_opt(
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
        except Exception as e:
            print(f"Inside IndicatorHelper.get_underlying_contract_and_all_strikes Exception: {e}")

        return underlying_contract, all_strikes

    @staticmethod
    def get_list_of_call_and_put_option_contracts(
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
    ):
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
                    exchange=exchange,
                    currency=currency,
                    expiry_date=expiry,
                    strike_price=strike,
                    right=right,
                    multiplier=multiplier,
                    trading_class=trading_class,
                )

                if right == "CALL":
                    list_of_all_call_option_contracts.append(opt_contract)
                else:
                    list_of_all_put_option_contracts.append(opt_contract)

        return (
            list_of_all_call_option_contracts,
            list_of_all_put_option_contracts,
        )

    @staticmethod
    def get_mkt_data_df_for_call_and_put_options(
        list_of_all_call_option_contracts, list_of_all_put_option_contracts, snapshot, generic_tick_list
    ):
        """
        Loop for Call and put, reqMktData and return dataframes
        return call_option_mkt_data_df, put_option_mkt_data_df
        """

        # Option MKT Data DFs, PUT MKT Data DFs
        columns = [
            "Strike",
            "Delta",
            "ConId",
            "Bid",
            "Ask",
            "CallOI",
            "PutOI",
            "AskIV",
            "BidIV",
            "LastIV",
        ]

        call_option_mkt_data_df = pd.DataFrame()
        put_option_mkt_data_df = pd.DataFrame()

        call_list__ = ["Call", list_of_all_call_option_contracts]
        put_list__ = ["Put", list_of_all_put_option_contracts]

        flag_market_open = variables.flag_market_open

        # Loop for Call and put, reqMktData and return dataframes
        for indx in range(2):

            data_frame_dict = {col: [] for col in columns}

            list_of_all_option_contracts = list_of_all_call_option_contracts if indx == 0 else list_of_all_put_option_contracts
            # Fetch Data for all the Contracts
            list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple = asyncio.run(
                MarketDataFetcher.get_option_delta_and_implied_volatility_for_contracts_list_async(
                    list_of_all_option_contracts,
                    flag_market_open,
                    generic_tick_list=generic_tick_list,
                    snapshot=snapshot,
                )
            )

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

                data_frame_dict["Strike"].append(contract.strike)
                data_frame_dict["Delta"].append(delta)
                # data_frame_dict["ConId"].append(contract.conId)
                data_frame_dict["ConId"].append(None)
                data_frame_dict["Bid"].append(bid_price)
                data_frame_dict["Ask"].append(ask_price)
                data_frame_dict["CallOI"].append(call_oi)
                data_frame_dict["PutOI"].append(put_oi)
                data_frame_dict["AskIV"].append(iv_ask)
                data_frame_dict["BidIV"].append(iv_bid)
                data_frame_dict["LastIV"].append(iv_last)

            if indx == 0:
                call_option_mkt_data_df = pd.DataFrame(data_frame_dict)
            else:
                put_option_mkt_data_df = pd.DataFrame(data_frame_dict)

        return call_option_mkt_data_df, put_option_mkt_data_df

    @staticmethod
    def update_indicator_values_for_indcator_id(indicator_id: int, values_dict):
        """
        Update in DB, GUI, Sys everywhere
        """

        # TODO - rewrite
        values_dict_for_db = {}
        current_time = datetime.datetime.now(variables.target_timezone_obj)

        for key, value in values_dict.items():
            if value is None:
                continue
            values_dict_for_db[key] = f"{value}" + f"|{current_time}"

        where_condition = f" WHERE `indicator_id` = {indicator_id};"

        update_query = SqlQueries.create_update_query(
            table_name="indicator_table",
            values_dict=values_dict_for_db,
            where_clause=where_condition,
        )

        # Update values in rows
        res = SqlQueries.execute_update_query(update_query)

        # If unable to update return
        if not res:
            print(f"IV values not updated in DB", {indicator_id})
            # return
        
        # Update Values here
        if indicator_id in StrategyVariables.map_indicator_id_to_indicator_object:
            StrategyVariables.map_indicator_id_to_indicator_object[indicator_id].update_attr_value(values_dict_for_db)
        try:
            GUIUtils.update_indicator_row_in_gui(indicator_id)
        except Exception as e:
            print("Exception GUIUTILS", e)
