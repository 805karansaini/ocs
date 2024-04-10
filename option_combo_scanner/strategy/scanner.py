import asyncio
import copy
import datetime
import math
import pprint
import time
import traceback

import pandas as pd
from tabulate import tabulate

from com.contracts import get_contract, get_contract_details
from com.greeks import async_get_deltas
from com.option_comobo_scanner_idetif import (
    find_closest_expiry_for_fop_given_fut_expiries_and_trading_class,
    find_nearest_expiry_and_all_strikes_for_stk_given_dte,
    find_nearest_expiry_for_future_given_fut_dte)
from com.variables import variables
from option_combo_scanner.cache.data_store import DataStore
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.indicators_calculator.market_data_fetcher import \
    MarketDataFetcher
from option_combo_scanner.strategy.greeks_calculation import CalcluateGreeks
from option_combo_scanner.strategy.indicator import Indicator
from option_combo_scanner.strategy.max_loss_profit_calculation import MaxPNLCalculation
from option_combo_scanner.strategy.scanner_algo import ScannerAlgo
# from option_combo_scanner.strategy import strategy_variables
from option_combo_scanner.strategy.scanner_combination import \
    ScannerCombination
from option_combo_scanner.strategy.scanner_leg import ScannerLeg
from option_combo_scanner.strategy.strategy_variables import StrategyVariables


class Scanner:
    x = f"Scanner Class: scanner_combination_tab_obj".upper()
    print(x)

    scanner_combination_tab_obj = None
    scanner_indicator_tab_obj = None

    def __init__(
        self,
    ):
        self.local_map_instrument_id_to_instrument_object = copy.deepcopy(StrategyVariables.map_instrument_id_to_instrument_object)
        self.config_obj = copy.deepcopy(StrategyVariables.config_object)

    # def get_strike_and_closet_expiry_for_fop(
    #     self,
    #     symbol,
    #     dte,
    #     underlying_sec_type,
    #     exchange,
    #     currency,
    #     multiplier,
    #     trading_class,
    # ):
    #     """
    #     Function used to get the
    #     list of all the available strikes
    #     and closest expiry for FOP sec_type

    #     """

    #     # print(
    #     #     "Scanner: ",
    #     #     symbol,
    #     #     dte,
    #     #     underlying_sec_type,
    #     #     exchange,
    #     #     currency,
    #     #     multiplier,
    #     #     trading_class,
    #     # )

    #     # only call once (not for N-DTEs)
    #     all_fut_expiries = find_nearest_expiry_for_future_given_fut_dte(
    #         symbol,
    #         dte,
    #         underlying_sec_type,
    #         exchange,
    #         currency,
    #         multiplier,
    #         trading_class="",
    #         only_want_all_expiries=True,
    #     )

    #     # Handling None
    #     if all_fut_expiries == None:
    #         return None, None, None

    #     # get closest FOP Expiry for given Trading class
    #     (
    #         all_strikes,
    #         closest_expiry_date,
    #         underlying_conid,
    #     ) = find_closest_expiry_for_fop_given_fut_expiries_and_trading_class(
    #         symbol,
    #         dte,
    #         underlying_sec_type,
    #         exchange,
    #         currency,
    #         multiplier,
    #         trading_class,
    #         all_fut_expiries,
    #     )

    #     return all_strikes, closest_expiry_date, underlying_conid

    # def stop_scan(self):
    #     self.scanning = False
    def get_strike_and_closet_expiry_for_opt(
        self,
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
            string_of_strike_price,
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
        return string_of_strike_price, closest_expiry_date, underlying_conid

    def get_instrument_from_variables(
        self,
    ):
        local_map_instrument_id_to_instrument_object = copy.deepcopy(StrategyVariables.map_instrument_id_to_instrument_object)
        return local_map_instrument_id_to_instrument_object

    def get_config_from_variables(
        self,
    ):
        local_config_object = copy.deepcopy(StrategyVariables.config_object)

        return local_config_object

    def get_contract_from_instrument_object(self, instrument_obj):
        """
        1. Create Base contract
        """
        symbol = instrument_obj.symbol
        sec_type = instrument_obj.sec_type
        multiplier = instrument_obj.multiplier
        exchange = instrument_obj.exchange
        trading_class = instrument_obj.trading_class
        currency = instrument_obj.currency
        conid = instrument_obj.conid
        primary_exchange = instrument_obj.primary_exchange

        contract = get_contract(
            symbol=symbol,
            sec_type=sec_type,
            multiplier=multiplier,
            exchange=exchange,
            currency=currency,
        )
        return contract

    def get_list_contract_details(self, list_of_contracts):
        list_of_complete_contracts = []

        for contract in list_of_contracts:
            contract_details = get_contract_details(contract=contract)
            list_of_complete_contracts.append(contract_details)

        return list_of_complete_contracts

    def check_do_we_need_to_restart_scan(
        self,
    ):
        """
        False: Indicates do not need to restart scan
        True: Indicates do need to restart scan
        """
        # If config got changed
        local_config_object = self.get_config_from_variables()
        
        if local_config_object:
            if not self.config_obj.config_id == local_config_object.config_id:
                return True

        if StrategyVariables.flag_force_restart_scanner:
            return True

        return False

    def start_scanner(
        self,
    ):

        # Single Config
        # No. of Config Leg
        # for (leg_object) in self.config_obj.list_of_config_leg_object:
        #     print(leg_object)
        #     print(leg_object.instrument_id)



            # Early Termination of Scanner
            if self.check_do_we_need_to_restart_scan():
                print(f"Early Termination: {self.config_obj}")
                return

            # Skip this instrument if not exist anymore in system
            # if not leg_object.instrument_id in StrategyVariables.map_instrument_id_to_instrument_object:
            #     continue

            #  We need to loop over the configs now - IMPT V2 KARAN ARYAN 
            
            if self.config_obj is None:
                return
            list_of_all_generated_combination = self.generate_combinations()
            # todo early teminate
            if self.check_do_we_need_to_restart_scan():
                print(f"Early Termination: {self.config_obj}")
                return

            list_of_combo_net_deltas = self.get_list_combo_net_delta(list_of_all_generated_combination=list_of_all_generated_combination)
            # todo early teminate
            if self.check_do_we_need_to_restart_scan():
                print(f"Early Termination: {self.config_obj}")
                return
            # list_of_all_generated_combination Leg1: (symbol, strike, delta, conid, expiry, bid ask iv un conid, theta vega gmma, und_price)
            self.insert_combinations_into_db(list_of_all_generated_combination, list_of_combo_net_deltas)

            # right = None
            # list_of_dte = []
            # try:
            #     right = self.config_obj.right

            #     list_of_dte_string_form = self.config_obj.list_of_dte

            #     list_of_dte = [int(num.strip()) for num in list_of_dte_string_form.split(",")]
            # except AttributeError:
            #     # Handle the case where local_config_object does not have the expected attributes
            #     print(f"Add Configuration Values")

            # Based on sec_type wil run the scan for instrument
            # if sec_type == "OPT":
            #     self.run_scan_for_opt(
            #         instrument_object=instrument_object,
            #         list_of_dte=list_of_dte,
            #         right=right,
            #     )
            # elif sec_type == "FOP":
            #     self.run_scan_for_fop(
            #         instrument_object=instrument_object,
            #         list_of_dte=list_of_dte,
            #         right=right,
            #     )
            # else:
            #     print(f"Security Type {sec_type} is invalid for {instrument_object}")
            #     continue
                
    # Combination insertion into db
    def insert_combinations_into_db(self, list_of_all_generated_combination, list_of_combo_net_delta):
        config_obj = self.config_obj

        list_of_config_leg_object = config_obj.list_of_config_leg_object
        
        # Get all the combo_id for this very instrument and expiry pair(config_id)
        where_condition = (
            f" WHERE `config_id` = {config_obj.config_id};"
        )
        select_query = SqlQueries.create_select_query(
            table_name="combination_table",
            columns="`combo_id`",
            where_clause=where_condition,
        )

        all_combo_ids_for_instrument_and_expiry_from_db = SqlQueries.execute_select_query(select_query)
        _list_of_combo_ids = [_["combo_id"] for _ in all_combo_ids_for_instrument_and_expiry_from_db]

        # Delete Query
        delete_query = SqlQueries.create_delete_query(table_name="combination_table", where_clause=where_condition)
        res = SqlQueries.execute_delete_query(delete_query)

        # Remove from the system.
        Utils.remove_row_from_scanner_combination_table(list_of_combo_ids=_list_of_combo_ids)

        values_dict = {          
            "config_id": config_obj.config_id,
            "number_of_legs": config_obj.no_of_leg,
        }

        total_combo_profit = total_combo_loss = 0

        for combination, combo_net_delta in zip(list_of_all_generated_combination, list_of_combo_net_delta):
            
            # todo early teminate
            if self.check_do_we_need_to_restart_scan():
                print(f"Early Termination: {self.config_obj}")
                return
            # Calculate all greeks for the combo
            net_greek_dict = CalcluateGreeks.compute_all_greeks(combination, list_of_config_leg_object)
            print(f"list_of_greeks_dicts: {net_greek_dict}")

            for greek_key, greek_value in net_greek_dict.items():
                values_dict[greek_key] = round(greek_value, 5)

            # Extract new 4 values vega theta gamma und price and call maxpnl with previous tuple 
            modified_combination = [(combo_tuple[:-4]) for combo_tuple in combination]
            # Calulate Max Profit/Loss for the combination
            max_profit, max_loss = MaxPNLCalculation.calcluate_max_pnl(modified_combination, list_of_config_leg_object)
            
            total_combo_profit = round(max_profit, 2)
            total_combo_loss = round(max_loss,2)

            # Remove the key, val if exists form prev iter
            if "combo_id" in values_dict:
                del values_dict["combo_id"]

            # Remove the key, val if exists form prev iter
            if "list_of_all_leg_objects" in values_dict:
                del values_dict["list_of_all_leg_objects"]

        
            values_dict["combo_net_delta"] = combo_net_delta

            values_dict["max_profit"] = "inf" if max_profit == float("inf") else total_combo_profit
            values_dict["max_loss"] = "-inf" if max_loss == float("-inf") else total_combo_loss

            res, combo_id = SqlQueries.insert_into_db_table(table_name="combination_table", values_dict=values_dict)
            if not res:
                # print(f"Unable to insert Combination in the table: {combination}")
                continue
            list_of_all_leg_objects = []
            # insertion of the values in legs table
            for index, ((_, strike, delta, con_id, expiry, bid, ask, iv,und_conid,_,_,_,_), config_leg_object) in enumerate(zip(combination, list_of_config_leg_object)):

                instrument_id = config_leg_object.instrument_id
                instrument_object = copy.deepcopy(StrategyVariables.map_instrument_id_to_instrument_object[instrument_id])
                leg_values_dict = {
                    "combo_id": combo_id,
                    "leg_number": index + 1,
                    "con_id": con_id,
                    "strike": strike,
                    "qty": 1,
                    "delta_found": delta,
                    "expiry": expiry,
                    "action": config_leg_object.action,
                    "right": config_leg_object.right,
                    "symbol": instrument_object.symbol,
                    "sec_type": instrument_object.sec_type,
                    "trading_class": instrument_object.trading_class,
                    "multiplier": instrument_object.multiplier,
                    "exchange": instrument_object.exchange,
                    "currency": instrument_object.currency,
                    "primary_exchange": instrument_object.primary_exchange,
                    "underlying_conid": und_conid,
                }

                res, leg_id = SqlQueries.insert_into_db_table(table_name="legs_table", values_dict=leg_values_dict)
                if not res:
                    print(f"Unable to insert leg in the table: {leg_values_dict}")
                list_of_all_leg_objects.append(ScannerLeg(leg_values_dict))

            values_dict["combo_id"] = combo_id
            values_dict["list_of_all_leg_objects"] = list_of_all_leg_objects

            #  Scanner Combination Object
            scanner_combination_object = ScannerCombination(values_dict)
            Scanner.scanner_combination_tab_obj.insert_combination_in_scanner_combination_table_gui(scanner_combination_object)

    # Deletion of Indicator data  from DB/GUI
    def delete_indicator_row_from_db_gui_and_system(self, list_of_indicator_ids_deletion):
        for indicator_id in list_of_indicator_ids_deletion:
            where_condition = f"WHERE `indicator_id` = {indicator_id}"
            delete_query = SqlQueries.create_delete_query(table_name="indicator_table", where_clause=where_condition)
            res = SqlQueries.execute_delete_query(delete_query)

        # Remove from system
        if list_of_indicator_ids_deletion:
            Utils.remove_row_from_indicator_table(list_of_indicator_ids=list_of_indicator_ids_deletion)

    # def update_indicator_table_for_instrument(
    #     self,
    #     instrument_object,
    #     set_of_all_closest_expiry,
    #     map_closest_expiry_to_underlying_conid,
    # ):
    #     """Updates the indicator table for a given instrument."""

    #     exchange = instrument_object.exchange
    #     where_condition = f" WHERE `instrument_id` = {instrument_object.instrument_id};"
    #     select_query = SqlQueries.create_select_query(
    #         table_name="indicator_table",
    #         columns="`indicator_id`, `trading_class`, `expiry`",
    #         where_clause=where_condition,
    #     )

    #     # Get all the old rows from indicator table
    #     all_the_existing_rows_form_db_table = SqlQueries.execute_select_query(select_query)

    #     map_indicator_id_to_expiry_and_trading_class_str = {}
    #     map_expiry_and_trading_class_str_to_indicator_id = {}

    #     for old_indicator_dict in all_the_existing_rows_form_db_table:
    #         indicator_id = int(old_indicator_dict["indicator_id"])
    #         expiry_and_trading_class_str = f"{old_indicator_dict['expiry']}{old_indicator_dict['trading_class']}"

    #         map_indicator_id_to_expiry_and_trading_class_str[indicator_id] = expiry_and_trading_class_str
    #         map_expiry_and_trading_class_str_to_indicator_id[expiry_and_trading_class_str] = indicator_id

    #     # getting the new indicator_rows
    #     list_of_new_expiry_and_trading_class_str = []
    #     for expiry in set_of_all_closest_expiry:
    #         _temp = f"{expiry}{instrument_object.trading_class}"
    #         list_of_new_expiry_and_trading_class_str.append(_temp)

    #     list_of_indicator_ids_for_deletion = []

    #     # Lopping on old one
    #     for (
    #         exp_trad_cls,
    #         indicator_id,
    #     ) in map_expiry_and_trading_class_str_to_indicator_id.items():
    #         if not exp_trad_cls in list_of_new_expiry_and_trading_class_str:
    #             list_of_indicator_ids_for_deletion.append(indicator_id)

    #     # self.delete_indicator_row_from_db_gui_and_system(list_of_indicator_ids_for_deletion)
        
    #     if list_of_indicator_ids_for_deletion:
    #         self.delete_indicator_row_from_db_gui_and_system(list_of_indicator_ids_for_deletion)

    #     # Insert all new indicator row
    #     # old nahi hai, but new mai hai
    #     # LOOOPING ON NEW ONE
    #     for exp_trad_cls in list_of_new_expiry_and_trading_class_str:

    #         if exp_trad_cls in map_expiry_and_trading_class_str_to_indicator_id:
    #             continue

    #         # TODO Need underlying conid  TODO Comment
            
    #         # Extract expiry date from the expiry and trading class string
    #         expiry = exp_trad_cls[:8]
    #         # Retrieve the underlying contract ID associated with the closest expiry
    #         underlying_conid = map_closest_expiry_to_underlying_conid[int(expiry)]

    #         #  Create a dictionary containing information about the new instrument
    #         new_dict = {
    #             "instrument_id": instrument_object.instrument_id,
    #             "symbol": instrument_object.symbol,
    #             "sec_type": instrument_object.sec_type,
    #             "multiplier": instrument_object.multiplier,
    #             "trading_class": instrument_object.trading_class,
    #             "expiry": expiry,
    #             "underlying_conid": underlying_conid,
    #             "exchange": exchange,
    #         }

    #          # Insert the new indicator row in the database (GUI and system)
    #         self.insert_new_indicator_row_in_db_gui_and_system(new_dict, instrument_object)

    # Insertion of new indicator row in DB/GUI
    def insert_new_indicator_row_in_db_gui_and_system(self, values_dict, instrument_object):
        # if instrument_id, expiry exist in indcator table continue else insertion
        res, indicator_id = SqlQueries.insert_into_db_table(table_name="indicator_table", values_dict=values_dict)
        if not res:
            return
        values_dict["indicator_id"] = indicator_id
        indicator_obj = Indicator(values_dict)

        # Insertion of indicator data in GUI
        Scanner.scanner_indicator_tab_obj.insert_into_indicator_table(indicator_obj)

    # def run_scan_for_opt(self, instrument_object, list_of_dte, right):
    #     symbol = instrument_object.symbol
    #     sec_type = instrument_object.sec_type
    #     multiplier = instrument_object.multiplier
    #     exchange = instrument_object.exchange
    #     trading_class = instrument_object.trading_class
    #     currency = instrument_object.currency
    #     conid = instrument_object.conid
    #     primary_exchange = instrument_object.primary_exchange

    #     set_of_all_closest_expiry = set()
    #     all_strikes = None
    #     map_closest_expiry_to_underlying_conid = {}
    #     for dte in list_of_dte:

    #         # OPT/FOP
    #         # Get all the expiry from the list of DTE
    #         (
    #             all_strikes_string,
    #             closest_expiry,
    #             underlying_conid,
    #         ) = self.get_strike_and_closet_expiry_for_opt(
    #             symbol=symbol,
    #             dte=dte,
    #             underlying_sec_type="STK",
    #             exchange=exchange,
    #             currency=currency,
    #             multiplier=multiplier,
    #             trading_class="",
    #         )
    #         if all_strikes_string == None or closest_expiry == None:
    #             continue

    #         set_of_all_closest_expiry.add(closest_expiry)
    #         map_closest_expiry_to_underlying_conid[int(closest_expiry)] = underlying_conid

    #         # Removing  {  }
    #         all_strikes = [float(_) for _ in all_strikes_string[1:-1].split(",")]

    #         all_strikes = sorted(all_strikes)

    #     # TODO - Comment

    #     # Updates the indicator table for a given instrument
    #     self.update_indicator_table_for_instrument(
    #         instrument_object,
    #         set_of_all_closest_expiry,
    #         map_closest_expiry_to_underlying_conid,
    #     )

    #     # Early Termination of Scanner
    #     if self.check_do_we_need_to_restart_scan():
    #         print(f"Early Termination: {self.config_obj}")
    #         return

    #     for expiry in set_of_all_closest_expiry:
    #         # print("All Strike: ", all_strikes)

    #         list_of_all_option_contracts = []
    #         for strike in all_strikes:
    #             list_of_all_option_contracts.append(
    #                 get_contract(
    #                     symbol=symbol,
    #                     sec_type=sec_type,
    #                     multiplier=multiplier,
    #                     exchange=exchange,
    #                     currency=currency,
    #                     right=right,
    #                     strike_price=strike,
    #                     expiry_date=expiry,
    #                     trading_class=None,
    #                 )
    #             )

    #         # Fetch Data for all the  Contracts
    #         list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_tuple = asyncio.run(
    #             MarketDataFetcher.get_option_delta_and_implied_volatility_for_contracts_list_async(
    #                 list_of_all_option_contracts,
    #                 flag_market_open=False,
    #                 generic_tick_list="",
    #             )
    #         )

    #         columns = [
    #             "Strike",
    #             "Delta",
    #             "ConId",
    #             "Bid",
    #             "Ask",
    #         ]
    #         data_frame_dict = {col: [] for col in columns}

    #         for contract, (
    #             delta,
    #             iv_ask,
    #             iv_bid,
    #             iv_last,
    #             bid_price,
    #             ask_price,
    #             call_oi,
    #             put_oi,
    #         ) in zip(
    #             list_of_all_option_contracts,
    #             list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_tuple,
    #         ):
    #             data_frame_dict["Strike"].append(contract.strike)
    #             data_frame_dict["Delta"].append(str(delta))
    #             data_frame_dict["ConId"].append(contract.conId)

    #             data_frame_dict["Bid"].append(bid_price)
    #             data_frame_dict["Ask"].append(ask_price)

    #         df = pd.DataFrame(data_frame_dict)
    #         # print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))

    #         # Early Termination of Scanner
    #         if self.check_do_we_need_to_restart_scan():
    #             print(f"Early Termination: {self.config_obj}")
    #             return

    #         list_of_all_generated_combination = self.generate_combinations(
    #             strike_and_delta_dataframe=df,
    #         )

    #         # pprint.pprint(f"list_of_all_generated_combination :{list_of_all_generated_combination}")

    #         # Early Termination of Scanner
    #         if self.check_do_we_need_to_restart_scan():
    #             print(f"Early Termination: {self.config_obj}")
    #             return

    #         list_of_combo_net_deltas = self.get_list_combo_net_delta(list_of_all_generated_combination=list_of_all_generated_combination)

    #         # Early Termination of Scanner
    #         if self.check_do_we_need_to_restart_scan():
    #             print(f"Early Termination: {self.config_obj}")
    #             return

    #         self.insert_combinations_into_db(
    #             list_of_all_generated_combination,
    #             instrument_object,
    #             expiry,
    #             list_of_combo_net_deltas,
    #             df,
    #         )

    # def run_scan_for_fop(self, instrument_object, list_of_dte, right):
    #     symbol = instrument_object.symbol
    #     sec_type = instrument_object.sec_type
    #     multiplier = instrument_object.multiplier
    #     exchange = instrument_object.exchange
    #     trading_class = instrument_object.trading_class
    #     currency = instrument_object.currency
    #     conid = instrument_object.conid
    #     primary_exchange = instrument_object.primary_exchange

    #     set_of_all_closest_expiry = set()
    #     all_strikes = None
    #     map_closest_expiry_to_underlying_conid = {}

    #     for dte in list_of_dte:

    #         # OPT/FOP
    #         # Get all the expiry from the list of DTE
    #         (
    #             all_strikes,
    #             closest_expiry,
    #             underlying_conid,
    #         ) = self.get_strike_and_closet_expiry_for_fop(
    #             symbol=symbol,
    #             dte=dte,
    #             underlying_sec_type="FUT",
    #             exchange=exchange,
    #             currency=currency,
    #             multiplier=multiplier,
    #             trading_class=trading_class,
    #         )

    #         # print("Scanner: FOP underlying_coind:", underlying_conid)
    #         if all_strikes is None or closest_expiry == None:
    #             continue

    #         map_closest_expiry_to_underlying_conid[int(closest_expiry)] = underlying_conid
    #         set_of_all_closest_expiry.add(closest_expiry)

    #     # Update Indicator table with Unique Rows
    #     self.update_indicator_table_for_instrument(
    #         instrument_object,
    #         set_of_all_closest_expiry,
    #         map_closest_expiry_to_underlying_conid,
    #     )

    #     # Early Termination of Scanner
    #     if self.check_do_we_need_to_restart_scan():
    #         print(f"Early Termination: {self.config_obj}")
    #         return

    #     for expiry in set_of_all_closest_expiry:
    #         # print("All Strike: ", all_strikes)

    #         list_of_all_option_contracts = []
    #         for strike in all_strikes:
    #             list_of_all_option_contracts.append(
    #                 get_contract(
    #                     symbol=symbol,
    #                     sec_type=sec_type,
    #                     multiplier=multiplier,
    #                     exchange=exchange,
    #                     currency=currency,
    #                     right=right,
    #                     strike_price=strike,
    #                     expiry_date=expiry,
    #                     trading_class=trading_class,
    #                 )
    #             )

    #         # Fetch Data for all the  Contracts
    #         list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_tuple = asyncio.run(
    #             MarketDataFetcher.get_option_delta_and_implied_volatility_for_contracts_list_async(
    #                 list_of_all_option_contracts,
    #                 flag_market_open=False,
    #                 generic_tick_list="",
    #             )
    #         )

    #         # pprint.pprint(list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_tuple)

    #         columns = [
    #             "Strike",
    #             "Delta",
    #             "ConId",
    #             "Bid",
    #             "Ask",
    #         ]
    #         data_frame_dict = {col: [] for col in columns}

    #         for contract, (
    #             delta,
    #             iv_ask,
    #             iv_bid,
    #             iv_last,
    #             bid_price,
    #             ask_price,
    #             call_oi,
    #             put_oi,
    #         ) in zip(
    #             list_of_all_option_contracts,
    #             list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_tuple,
    #         ):
    #             data_frame_dict["Strike"].append(contract.strike)
    #             data_frame_dict["Delta"].append(str(delta))
    #             data_frame_dict["ConId"].append(contract.conId)

    #             data_frame_dict["Bid"].append(bid_price)
    #             data_frame_dict["Ask"].append(ask_price)

    #         df = pd.DataFrame(data_frame_dict)
    #         # print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))

    #         # Early Termination of Scanner
    #         if self.check_do_we_need_to_restart_scan():
    #             print(f"Early Termination: {self.config_obj}")
    #             return

    #         list_of_all_generated_combination = self.generate_combinations(
    #             strike_and_delta_dataframe=df,
    #         )

    #         # pprint.pprint(f"list_of_all_generated_combination :{list_of_all_generated_combination}")

    #         # Early Termination of Scanner
    #         if self.check_do_we_need_to_restart_scan():
    #             print(f"Early Termination: {self.config_obj}")
    #             return

    #         # Get the list of net combo delta for the list of combinations
    #         list_of_combo_net_deltas = self.get_list_combo_net_delta(list_of_all_generated_combination=list_of_all_generated_combination)

    #         # Early Termination of Scanner
    #         if self.check_do_we_need_to_restart_scan():
    #             print(f"Early Termination: {self.config_obj}")
    #             return

    #         self.insert_combinations_into_db(
    #             list_of_all_generated_combination,
    #             instrument_object,
    #             expiry,
    #             list_of_combo_net_deltas,
    #             df,
    #         )

    def generate_combinations(self, ):

        # Get the configurations
        
        remaining_no_of_legs = self.config_obj.no_of_leg - 1
        delta_range_low = self.config_obj.list_of_config_leg_object[0].delta_range_min
        delta_range_high = self.config_obj.list_of_config_leg_object[0].delta_range_max
        leg_object = self.config_obj.list_of_config_leg_object[0]
       
        print(leg_object)
        # print("\nGenerate Combintaions: ")
        # print(tabulate(strike_and_delta_dataframe, headers="keys", tablefmt="psql", showindex=False))
        current_date = datetime.datetime.now(variables.target_timezone_obj)
        # List
        res = ScannerAlgo(
            config_obj=self.config_obj,
        ).run_scanner(
            remaining_no_of_legs,
            delta_range_low,
            delta_range_high,
            current_date,
            leg_object
        )

        return res

    # Function to insertion the combination in the database
    # def insert_combinations_into_db(
    #     self,
    #     list_of_all_generated_combination,
    #     instrument_object,
    #     expiry,
    #     list_of_combo_net_deltas,
    #     df_with_strike_delta_bid_ask,
    # ):

    #     config_obj = self.config_obj
    #     list_of_config_leg_object = config_obj.list_of_config_leg_object

    #     # Get all the combo_id for this very instrument and expiry pair(config_id)
    #     where_condition = (
    #         f" WHERE `config_id` = {config_obj.config_id} AND `instrument_id` = {instrument_object.instrument_id} AND `expiry` = {expiry};"
    #     )
    #     select_query = SqlQueries.create_select_query(
    #         table_name="combination_table",
    #         columns="`combo_id`",
    #         where_clause=where_condition,
    #     )

    #     all_combo_ids_for_instrument_and_expiry_from_db = SqlQueries.execute_select_query(select_query)
    #     _list_of_combo_ids = [_["combo_id"] for _ in all_combo_ids_for_instrument_and_expiry_from_db]

    #     # Delete Query
    #     delete_query = SqlQueries.create_delete_query(table_name="combination_table", where_clause=where_condition)
    #     res = SqlQueries.execute_delete_query(delete_query)

    #     # Remove from the system.
    #     Utils.remove_row_from_scanner_combination_table(list_of_combo_ids=_list_of_combo_ids)

    #     values_dict = {
    #         "instrument_id": instrument_object.instrument_id,
    #         "config_id": config_obj.config_id,
    #         "number_of_legs": config_obj.no_of_leg,
    #         "symbol": instrument_object.symbol,
    #         "sec_type": instrument_object.sec_type,
    #         "expiry": expiry,
    #         "right": config_obj.right,
    #         "multiplier": instrument_object.multiplier,
    #         "trading_class": instrument_object.trading_class,
    #         "currency": instrument_object.currency,
    #         "exchange": instrument_object.exchange,
    #         # "max_profit_max_loss_ratio": 1.3,
    #         "primary_exchange": instrument_object.primary_exchange,
    #     }

    #     for combination, combo_net_delta in zip(list_of_all_generated_combination, list_of_combo_net_deltas):

    #         # print(f"\n Symbol: {instrument_object.symbol} Combination: {combination}")

    #         # TODO max loss/profit
    #         max_loss, max_profit = self.get_combination_max_loss_and_max_profit(
    #             list_of_legs_tuple=combination,
    #             list_of_config_leg_objects=list_of_config_leg_object,
    #             right=config_obj.right,
    #             multiplier=instrument_object.multiplier,
    #             df_with_strike_delta_bid_ask=df_with_strike_delta_bid_ask,
    #         )

    #         # Remove the key, val if exists form prev iter
    #         if "combo_id" in values_dict:
    #             del values_dict["combo_id"]

    #         # Remove the key, val if exists form prev iter
    #         if "list_of_all_leg_objects" in values_dict:
    #             del values_dict["list_of_all_leg_objects"]

    #         # add combo net delta calculation to the value dict
    #         values_dict["combo_net_delta"] = combo_net_delta
    #         values_dict["max_profit"] = "inf" if max_profit == float("inf") else max_profit
    #         values_dict["max_loss"] = "-inf" if max_loss == float("-inf") else max_loss
    #         res, combo_id = SqlQueries.insert_into_db_table(table_name="combination_table", values_dict=values_dict)
    #         if not res:
    #             # print(f"Unable to insert Combination in the table: {combination}")
    #             continue

    #         # list of leg object
    #         list_of_all_leg_objects = []
    #         for index, ((strike, delta, con_id), config_leg_object) in enumerate(zip(combination, list_of_config_leg_object)):
    #             leg_values_dict = {
    #                 "combo_id": combo_id,
    #                 "leg_number": index + 1,
    #                 "con_id": con_id,
    #                 "strike": strike,
    #                 "qty": 1,
    #                 "delta_found": delta,
    #                 "action": config_leg_object.action,
    #                 "delta_range_min": config_leg_object.delta_range_min,
    #                 "delta_range_max": config_leg_object.delta_range_max,
    #             }
    #             res, leg_id = SqlQueries.insert_into_db_table(table_name="legs_table", values_dict=leg_values_dict)
    #             if not res:
    #                 print(f"Unable to insert leg in the table: {leg_values_dict}")

    #             list_of_all_leg_objects.append(ScannerLeg(leg_values_dict))

    #         # Add the combo_id and leg objects
    #         values_dict["combo_id"] = combo_id
    #         values_dict["list_of_all_leg_objects"] = list_of_all_leg_objects

    #         # Scanner Combination Object
    #         scanner_combination_object = ScannerCombination(values_dict)

    #         # Insert the Scanner combination in GUI
    #         Scanner.scanner_combination_tab_obj.insert_combination_in_scanner_combination_table_gui(scanner_combination_object)
    #     Scanner.scanner_combination_tab_obj.filter_combo_based_on_max_loss_and_max_profit()

    # Function to calculate the leg wise option payoff
    def option_payoff(
        self,
        option_strike,
        option_type,
        buy_or_sell,
        quantity,
        underlying_price_expiry,
        combination_multiplier,
        leg_premium,
    ):
        """
        option_strike: Strike of the Leg
        option_type: CALL/PUT
        buy_or_sell: BUY/SELL
        quantity: Qty of Leg
        underlying_price_expiry: Price of option at expiry
        """
        leg_premium_received = 0
        # TODO Remove it
        payoff = 0

        if option_type == "CALL":
            if buy_or_sell == "BUY":

                # CALL BUY
                if underlying_price_expiry >= option_strike:
                    payoff += quantity * (underlying_price_expiry - option_strike) * combination_multiplier
                else:
                    payoff += 0

            else:

                # CALL SELL
                if underlying_price_expiry >= option_strike:
                    payoff -= quantity * (underlying_price_expiry - option_strike) * combination_multiplier
                else:
                    payoff += 0

        else:
            if buy_or_sell == "BUY":

                # BUY PUT
                if underlying_price_expiry >= option_strike:
                    payoff += 0
                else:
                    payoff += quantity * (option_strike - underlying_price_expiry) * combination_multiplier

            else:

                # SELL PUT
                if underlying_price_expiry >= option_strike:
                    payoff += 0
                else:
                    payoff -= quantity * (option_strike - underlying_price_expiry) * combination_multiplier

        # Consider the Option Premium as well
        if buy_or_sell == "BUY":
            leg_premium_received -= leg_premium * combination_multiplier
        else:
            leg_premium_received += leg_premium * combination_multiplier

        return payoff, leg_premium_received

    # Get the maxloss maxprofit for the combination (can work as each leg in group)
    def get_combination_max_loss_and_max_profit(
        self,
        list_of_legs_tuple,
        list_of_config_leg_objects,
        right,
        multiplier,
        df_with_strike_delta_bid_ask,
    ):
        # print("")
        max_profit = float("-inf")
        max_loss = float("inf")
        slope_left = 0
        slope_right = 0

        # Sort list_of_legs_tuple
        sorted_legs_tuple = sorted(
            list_of_legs_tuple, key=lambda x: x[0]
        )  # Assuming tuple elements to be sorted based on the first element

        # Rearrange list_of_config_leg_objects based on the sorting of list_of_legs_tuple
        sorted_indices = [list_of_legs_tuple.index(leg) for leg in sorted_legs_tuple]
        sorted_config_leg_objects = [list_of_config_leg_objects[i] for i in sorted_indices]

        list_of_legs_tuple = sorted_legs_tuple
        list_of_config_leg_objects = sorted_config_leg_objects
        for i, leg_tuple in enumerate(list_of_legs_tuple):
            """
            Leg: (Strike, Delta, Conid) # TOO Aryan
            """

            # Get the combination payoff for the strike of current leg
            combo_pay_off_for_current_strike, combination_premium_received = self.get_combination_payoff(
                list_of_legs_tuple,
                list_of_config_leg_objects,
                leg_tuple[0],
                right,
                multiplier,
                df_with_strike_delta_bid_ask,
            )
            # print(f"    UndPrice At Expiry {leg_tuple[0]}, Combination Payoff: {combo_pay_off_for_current_strike}")

            combo_pay_off_for_current_strike = round(combo_pay_off_for_current_strike)

            # Max Profit is max of (Payoff Strike1, PayoffStrike2...)
            max_profit = max(max_profit, combo_pay_off_for_current_strike)
            max_loss = min(max_loss, combo_pay_off_for_current_strike)

            # Get the Slope left for Strike 1
            if i == 0:
                # Strike1 - 1%: Get the previous Strike payoff for Strike1 - 1%
                prev_strike_payoff, combination_premium_received = self.get_combination_payoff(
                    list_of_legs_tuple,
                    list_of_config_leg_objects,
                    list_of_legs_tuple[i][0] * 0.99,
                    right,
                    multiplier,
                    df_with_strike_delta_bid_ask,
                )

                slope_left = prev_strike_payoff - combo_pay_off_for_current_strike

                # Edge Case
                if -0.0001 <= slope_left <= 0.0001:
                    slope_left = 0

                # print(
                #     f"    UndPrice At Expiry {list_of_legs_tuple[i][0] * 0.99}, Combination Payoff: {combo_pay_off_for_current_strike} SlopeLeft: {slope_left}"
                # )

            # Get the Slope Right for Strike N
            if i == len(list_of_legs_tuple) - 1:
                # StrikeN + 1%: Get the next Strike payoff for StrikeN + 1%
                next_strike_payoff, combination_premium_received = self.get_combination_payoff(
                    list_of_legs_tuple,
                    list_of_config_leg_objects,
                    list_of_legs_tuple[i][0] * 1.01,
                    right,
                    multiplier,
                    df_with_strike_delta_bid_ask,
                )
                slope_right = next_strike_payoff - combo_pay_off_for_current_strike

                # Edge Case:
                if -0.0001 <= slope_right <= 0.0001:
                    slope_right = 0

                # print(
                #     f"    UndPrice At Expiry {list_of_legs_tuple[i][0] * 1.01}, Combination Payoff: {combo_pay_off_for_current_strike} SlopeRight: {slope_right}"
                # )

                # print(f"LegTuple: {leg_tuple} {combo_pay_off_for_current_strike=} {next_strike_payoff=} {slope_right=}")

        # print(f"Combo: {max_profit=} {max_loss=} {slope_left=} {slope_right=}")
        # print("")

        # Final Premium
        max_profit += round(combination_premium_received, 2)
        max_loss += round(combination_premium_received, 2)

        if slope_right > 0 or slope_left > 0:
            max_profit = float("inf")

        if slope_right < 0 or slope_left < 0:
            max_loss = float("-inf")


        return max_loss, max_profit

    # Calulating Combination Payoff for Strike (each strike in leg with dte thing and theo price here in this func)
    def get_combination_payoff(
        self,
        list_of_legs_tuple,
        list_of_config_leg_object,
        underlying_strike_price,
        right,
        multiplier,
        df_with_strike_delta_bid_ask,
    ):
        combination_premium_received = 0
        combination_payoff = 0
        for leg, config_leg_obj in zip(list_of_legs_tuple, list_of_config_leg_object):
            instrument_id = config_leg_obj.instrument_id
            instrument_object_for_leg_prem = copy.deepcopy(StrategyVariables.map_instrument_id_to_instrument_object[instrument_id])
            option_strike,_, _, _, bid, ask = leg
            # option_strike = leg[0]

            leg_premium = 0
            try:

                # bid_value, ask_value = tuple(
                #     df_with_strike_delta_bid_ask[df_with_strike_delta_bid_ask["Strike"] == float(option_strike)][["Bid", "Ask"]].iloc[0]
                # )
                if bid == float("nan") or ask == float("nan"):
                    leg_premium = 0
                else:
                    leg_premium = (bid + ask) / 2

            except Exception as e:
                # TODO REMOVE IT
                print(f"Could not get the bid and ask for Strike: {option_strike}")
            leg_payoff, leg_premium_received = self.option_payoff(
                option_strike,
                config_leg_obj.right,
                config_leg_obj.action,
                1,
                underlying_strike_price,
                int(instrument_object_for_leg_prem.multiplier),
                leg_premium,
            )

            # print(f"Leg PayOff: {leg_payoff} Strike: {option_strike} Premium: {leg_premium}")
            combination_payoff += leg_payoff
            combination_premium_received += leg_premium_received
        return combination_payoff, combination_premium_received

    # Calulation of Combo Net Delta
    def get_list_combo_net_delta(self, list_of_all_generated_combination):

        list_of_config_leg_object = self.config_obj.list_of_config_leg_object
        list_of_combo_net_deltas = []
        # Loop over list of combination
        for combination in list_of_all_generated_combination:
            net_combo = 0
            # Loop over leg object to get action for the leg
            for leg_tuple, leg_object in zip(combination, list_of_config_leg_object):
                action = leg_object.action
                _,_, delta, _, _, _, _,_, _,_,_,_,_ = leg_tuple
                # if Buy will add the delta
                if action.upper() == "Buy".upper():
                    net_combo += delta
                # If Sell will substract the delta
                else:
                    net_combo -= delta
            net_combo = f"{float(net_combo):,.4f}"
            list_of_combo_net_deltas.append(net_combo)
        return list_of_combo_net_deltas


def run_option_combo_scanner():
    """
    pass

    """
    StrategyVariables.flag_force_restart_scanner = False
    last_scanned_time = None

    while True:
        current_time = time.time()

        try:

            if (
                StrategyVariables.flag_force_restart_scanner
                or last_scanned_time is None
                or current_time - last_scanned_time > StrategyVariables.rescan_time_in_seconds
            ):
                StrategyVariables.flag_force_restart_scanner = False

                try:
                    scanner_object = Scanner()
                    scanner_object.start_scanner()
                except Exception as e:
                    # Print the traceback
                    traceback.print_exc()

                # Update last_time
                last_scanned_time = time.time()

        except Exception as e:
            print(f"Inside run_option_combo_scanner: {e}")

        time.sleep(1)
