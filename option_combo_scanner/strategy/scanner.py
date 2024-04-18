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
    find_nearest_expiry_for_future_given_fut_dte,
)
from com.variables import variables
from option_combo_scanner.cache.data_store import DataStore
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.indicators_calculator.market_data_fetcher import MarketDataFetcher
from option_combo_scanner.strategy.greeks_calculation import CalcluateGreeks
from option_combo_scanner.strategy.indicator import Indicator
from option_combo_scanner.strategy.max_loss_profit_calculation import MaxPNLCalculation
from option_combo_scanner.strategy.scanner_algo import ScannerAlgo

# from option_combo_scanner.strategy import strategy_variables
from option_combo_scanner.strategy.scanner_combination import ScannerCombination
from option_combo_scanner.strategy.scanner_leg import ScannerLeg
from option_combo_scanner.strategy.strategy_variables import StrategyVariables


class Scanner:

    scanner_combination_tab_obj = None
    scanner_indicator_tab_obj = None

    def __init__(
        self,
    ):
        self.local_map_instrument_id_to_instrument_object = copy.deepcopy(StrategyVariables.map_instrument_id_to_instrument_object)
        self.config_obj = None  # copy.deepcopy(StrategyVariables.config_object)
        self.local_config_id_to_config_obj = copy.deepcopy(StrategyVariables.map_config_id_to_config_object)


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

        for config_id, config_obj in self.local_config_id_to_config_obj.items():
            if config_id not in StrategyVariables.map_config_id_to_config_object:
                print(f"Inside Start Scanner: Config id {config_id} does not exist")
                continue
            self.config_obj = config_obj
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

    # Combination insertion into db
    def insert_combinations_into_db(self, list_of_all_generated_combination, list_of_combo_net_delta):
        config_obj = self.config_obj

        list_of_config_leg_object = config_obj.list_of_config_leg_object

        # Get all the combo_id for this very instrument and expiry pair(config_id)
        where_condition = f" WHERE `config_id` = {config_obj.config_id};"
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
            # print(f"list_of_greeks_dicts: {net_greek_dict}")

            for greek_key, greek_value in net_greek_dict.items():
                values_dict[greek_key] = round(greek_value, 3)

            # Extract new 4 values vega theta gamma und price and call maxpnl with previous tuple
            modified_combination = [(combo_tuple[:-4]) for combo_tuple in combination]
            # Calulate Max Profit/Loss for the combination
            max_profit, max_loss = MaxPNLCalculation.calcluate_max_pnl(modified_combination, list_of_config_leg_object)

            total_combo_profit = round(max_profit, 2)
            total_combo_loss = round(max_loss, 2)

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
            for index, ((_, strike, delta, con_id, expiry, bid, ask, iv, und_conid, _, _, _, _), config_leg_object) in enumerate(
                zip(combination, list_of_config_leg_object)
            ):

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

    def generate_combinations(
        self,
    ):

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
        ).run_scanner(remaining_no_of_legs, delta_range_low, delta_range_high, current_date, leg_object)

        return res

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
                _, _, delta, _, _, _, _, _, _, _, _, _, _ = leg_tuple
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
