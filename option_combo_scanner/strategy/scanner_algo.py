import asyncio
import copy
import datetime
import time
import traceback
from functools import cache

import pandas as pd

from com.contracts import get_contract
from com.option_comobo_scanner_idetif import (
    find_closest_expiry_for_fop_given_fut_expiries_and_trading_class,
    find_nearest_expiry_and_all_strikes_for_stk_given_dte,
    find_nearest_expiry_for_future_given_fut_dte,
)
from option_combo_scanner.cache.data_store import DataStore
from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.indicators_calculator.helper_indicator import IndicatorHelper
from option_combo_scanner.indicators_calculator.market_data_fetcher import MarketDataFetcher
from option_combo_scanner.strategy.indicator import Indicator

# from option_combo_scanner.strategy.scanner import Scanner
from option_combo_scanner.strategy.strategy_variables import StrategyVariables

scanner_logger = CustomLogger.scanner_logger


class ScannerAlgo:
    scanner_indicator_tab_obj = None

    # def __init__(self):
    def __init__(self, config_obj, config_id):
        self.config_obj = config_obj
        self.config_id = config_id

    def get_strike_and_closet_expiry_for_fop(
        self,
        symbol,
        dte,
        underlying_sec_type,
        exchange,
        currency,
        multiplier,
        trading_class,
        low_range_date_str=None,
        high_range_date_str=None,
    ):
        """
        Function used to get the
        list of all the available strikes
        and closest expiry for FOP sec_type

        """

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
            return None, None, None, None

        # get closest FOP Expiry for given Trading class
        (
            all_strikes,
            closest_expiry_date,
            underlying_conid,
            expiry_date_in_range,
        ) = find_closest_expiry_for_fop_given_fut_expiries_and_trading_class(
            symbol,
            dte,
            underlying_sec_type,
            exchange,
            currency,
            multiplier,
            trading_class,
            all_fut_expiries,
            low_range_date_str,
            high_range_date_str,
        )

        return all_strikes, closest_expiry_date, underlying_conid, expiry_date_in_range

    def insert_new_indicator_row_in_db_gui_and_system(self, values_dict):

        res, indicator_id = SqlQueries.insert_into_db_table(table_name="indicator_table", values_dict=values_dict)
        if not res:
            scanner_logger.info(
                f"      Config ID: {self.config_id}  Inside ScannerAlgo.insert_new_indicator_row_in_db_gui_and_system, Insertion Result for Indicator Row: {res} Indicator ID: {indicator_id}"
            )
            return

        values_dict["indicator_id"] = indicator_id
        indicator_obj = Indicator(values_dict)

        # Insertion of indicator data in GUI
        ScannerAlgo.scanner_indicator_tab_obj.insert_into_indicator_table(indicator_obj)

    def delete_row_in_config_indicator_relation_db(self, list_of_config_relation_tuple_for_deletion):

        # Looping Over config-indicaor-relation-tuple and deleting those
        for config_id, leg_number, instrument_id, expiry in list_of_config_relation_tuple_for_deletion:
            where_condition = f" WHERE `config_id` = {config_id} AND `instrument_id` = {instrument_id} AND `expiry` = {expiry};"

            # Delete Query
            delete_query = SqlQueries.create_delete_query(table_name="config_indicator_relation", where_clause=where_condition)
            res = SqlQueries.execute_delete_query(delete_query)

            scanner_logger.info(
                f"      Config ID: {self.config_id}  Inside ScannerAlgo.delete_row_in_config_indicator_relation_db, InstrumentID: {instrument_id}, Deletion Result: {res} <{config_id, instrument_id, expiry}> "
            )

    # Insert row for instrumenent-config-indicator relationship table
    def insert_row_in_config_indicator_relation_db(self, values_dict):
        res, indicator_id = SqlQueries.insert_into_db_table(table_name="config_indicator_relation", values_dict=values_dict)
        return res

    def delete_indicator_row_from_db_gui_and_system(self, list_of_indicator_ids_deletion):
        for indicator_id in list_of_indicator_ids_deletion:
            where_condition = f"WHERE `indicator_id` = {indicator_id}"
            delete_query = SqlQueries.create_delete_query(table_name="indicator_table", where_clause=where_condition)
            res = SqlQueries.execute_delete_query(delete_query)

        # Remove from system
        if list_of_indicator_ids_deletion:
            Utils.remove_row_from_indicator_table(list_of_indicator_ids=list_of_indicator_ids_deletion)

    def get_strike_and_closet_expiry_for_opt(
        self,
        symbol,
        dte,
        underlying_sec_type,
        exchange,
        currency,
        multiplier,
        trading_class,
        low_range_date_str,
        high_range_date_str,
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
            expiry_date_in_range,
        ) = find_nearest_expiry_and_all_strikes_for_stk_given_dte(
            ticker=symbol,
            days_to_expiry=dte,
            underlying_sec_type=underlying_sec_type,
            exchange=exchange,
            currency=currency,
            multiplier=multiplier,
            fop_trading_class=trading_class,
            low_range_date_str=low_range_date_str,
            high_range_date_str=high_range_date_str,
        )
        return string_of_strike_price, closest_expiry_date, underlying_conid, expiry_date_in_range

    # d
    def filter_dataframe(self):
        """
        Removes all None and NaN values from self.strike_and_delta_dataframe
        and converts the remaining values to float.

        Args:
            self: reference to the current instance of the class

        Returns:
            None
        """

        # Drop rows with NaN values
        self.strike_and_delta_dataframe = self.strike_and_delta_dataframe.dropna()

        # Replace 'None' with NaN
        self.strike_and_delta_dataframe = self.strike_and_delta_dataframe.replace("None", float("nan"))

        # Convert values to float
        self.strike_and_delta_dataframe = self.strike_and_delta_dataframe.apply(pd.to_numeric, errors="coerce")

        # Converting Delta values to absolute
        self.strike_and_delta_dataframe["Delta"] = self.strike_and_delta_dataframe["Delta"].abs()

        # Remove all the row that have delta less than min_delta_threshold
        if StrategyVariables.flag_enable_filter_based_delta_threshold:
            self.strike_and_delta_dataframe = self.strike_and_delta_dataframe[
                (self.strike_and_delta_dataframe["Delta"] > StrategyVariables.min_delta_threshold)
            ]

            # Remove all the row that have delta higher than max_delta_threshold
            self.strike_and_delta_dataframe = self.strike_and_delta_dataframe[
                (self.strike_and_delta_dataframe["Delta"] < StrategyVariables.max_delta_threshold)
            ]

    @staticmethod
    def get_key_from_contract_for_scanner_algo(symbol, expiry, sec_type, right, trading_class, multiplier, exchange):
        # right = contract.right.lower()
        key_string = f"ocs_mkt_{symbol}_{expiry}_{sec_type}_{right}_{multiplier}_{trading_class}_{exchange}".lower()
        return key_string

    def filter_strikes(self, delta_range_low, delta_range_high, current_expiry, remaining_no_of_legs, leg_object):
        """
        Filters strikes based on the given delta_range_low and delta_range_high.

        Args:
            self: reference to the current instance of the class
            delta_range_low (float): Lower bound of the delta range
            delta_range_high (float): Upper bound of the delta range

        Returns:
            pandas.DataFrame: Filtered dataframe containing strikes within the given delta range
        """
        # print(delta_range_low, delta_range_high, current_expiry)
        # todo early teminate

        scanner_logger.debug(f"")

        # Checking if we need to skip or restart scan
        if self.check_do_we_need_to_restart_scan() or self.check_do_we_need_to_skip_current_scan():
            return []

        # Get the all the details for contract creation
        instrument_id = int(leg_object.instrument_id)
        if instrument_id not in StrategyVariables.map_instrument_id_to_instrument_object:
            scanner_logger.info(
                f"Config ID: {self.config_id} Leg Number: {leg_number} Inside ScannerAlgo.filter_strikes, function could not find instrument id: {instrument_id}"
            )
            return []

        instrument_object = copy.deepcopy(StrategyVariables.map_instrument_id_to_instrument_object[instrument_id])
        min_dte = leg_object.dte_range_min
        max_dte = leg_object.dte_range_max
        right = leg_object.right
        leg_number = leg_object.leg_number

        symbol = instrument_object.symbol
        sec_type = instrument_object.sec_type
        multiplier = instrument_object.multiplier
        exchange = instrument_object.exchange
        trading_class = instrument_object.trading_class
        currency = instrument_object.currency

        set_of_all_closest_expiry = set()
        all_strikes = None
        list_of_filtered_legs_tuple = []
        map_closest_expiry_to_underlying_conid = {}
        # Get the low range date and high range date to get list of expiry
        low_range_date_str = (current_expiry + datetime.timedelta(days=min_dte)).strftime("%Y%m%d")
        high_range_date_str = (current_expiry + datetime.timedelta(days=max_dte)).strftime("%Y%m%d")

        scanner_logger.info(
            f"Config ID: {self.config_id} Leg Number: {leg_number} Inside ScannerAlgo.filter_strikes, InstrumentID: {instrument_id} LowDate: {low_range_date_str} HighDate: {high_range_date_str}"
        )

        if sec_type in ["FOP"]:

            if sec_type == "FOP":
                underlying_sec_type = "FUT"
            else:
                pass

            # get all the strikes and list of expiry
            (all_strikes, closest_expiry, underlying_conid, expiry_date_in_range) = self.get_strike_and_closet_expiry_for_fop(
                symbol=symbol,
                dte=1,
                underlying_sec_type=underlying_sec_type,
                exchange=exchange,
                currency=currency,
                multiplier=multiplier,
                trading_class=trading_class,
                low_range_date_str=low_range_date_str,
                high_range_date_str=high_range_date_str,
            )

            # For cases where any of this is None return a empty list
            if all_strikes is None or closest_expiry is None or underlying_conid is None or expiry_date_in_range is None:
                scanner_logger.info(
                    f"Config ID: {self.config_id}  Inside ScannerAlgo.filter_strikes, For Und SecType: {underlying_sec_type}, [all_strikes, closest_expiry, underlying_conid,] is None"
                )
                return []

            scanner_logger.info(
                f"Config ID: {self.config_id} Leg Number: {leg_number} Inside ScannerAlgo.filter_strikes, InstrumentID: {instrument_id} All Expiry in Range: {expiry_date_in_range}"
            )

            for closest_expiry in expiry_date_in_range:
                map_closest_expiry_to_underlying_conid[int(closest_expiry)] = underlying_conid

            self.update_indicator_table_for_instrument(
                instrument_object,
                expiry_date_in_range,
                map_closest_expiry_to_underlying_conid,
                leg_number,
            )

        elif sec_type in ["OPT", "IND"]:

            if sec_type == "OPT":
                underlying_sec_type = "STK"
            elif sec_type == "IND":
                underlying_sec_type = "IND"
            else:
                pass

            (
                all_strikes_string,
                closest_expiry,
                underlying_conid,
                expiry_date_in_range,
            ) = self.get_strike_and_closet_expiry_for_opt(
                symbol=symbol,
                dte=1,
                underlying_sec_type=underlying_sec_type,
                exchange=exchange,
                currency=currency,
                multiplier=multiplier,
                trading_class=trading_class,
                low_range_date_str=low_range_date_str,
                high_range_date_str=high_range_date_str,
            )

            # For cases where any of this is None return a empty list
            if all_strikes_string is None or closest_expiry is None or underlying_conid is None or expiry_date_in_range is None:
                scanner_logger.info(
                    f"Config ID: {self.config_id}  Inside ScannerAlgo.filter_strikes, For Und SecType: {underlying_sec_type}, [all_strikes, closest_expiry, underlying_conid,] is None"
                )
                return []

            scanner_logger.info(
                f"Config ID: {self.config_id} Leg Number: {leg_number} Inside ScannerAlgo.filter_strikes, InstrumentID: {instrument_id} All Expiry in Range: {expiry_date_in_range}"
            )

            all_strikes = [float(_) for _ in all_strikes_string[1:-1].split(",")]

            all_strikes = sorted(all_strikes)
            for closest_expiry in expiry_date_in_range:
                map_closest_expiry_to_underlying_conid[int(closest_expiry)] = underlying_conid

            # Update the indicator table for the given list of expiry
            self.update_indicator_table_for_instrument(
                instrument_object,
                expiry_date_in_range,
                map_closest_expiry_to_underlying_conid,
                leg_number,
            )

        # todo early teminate
        if self.check_do_we_need_to_restart_scan() or self.check_do_we_need_to_skip_current_scan():
            return []

        for expiry in expiry_date_in_range:
            # key: ocs_mkt_ symbol, expiry, sectype, right, trading_class, multiplier  exchange

            # todo early teminate
            if self.check_do_we_need_to_restart_scan() or self.check_do_we_need_to_skip_current_scan():
                return []

            # get the key for caching the raw dataframe
            key = ScannerAlgo.get_key_from_contract_for_scanner_algo(symbol, expiry, sec_type, right, trading_class, multiplier, exchange)
            # print(key)
            data_frame = DataStore.get_data(key)

            # print(data_frame)
            if data_frame is not None:
                df = data_frame.copy()
            else:
                # Get the list of call and put option contract
                list_of_call_option_contracts, list_of_put_option_contracts = IndicatorHelper.get_list_of_call_and_put_option_contracts(
                    symbol,
                    sec_type,
                    expiry,
                    None,
                    None,
                    exchange,
                    currency,
                    multiplier,
                    trading_class,
                    all_strikes,
                )

                # Only Get data for single right, call or put depending on the leg config
                if right.upper() == "CALL":
                    list_of_put_option_contracts = []
                else:
                    list_of_call_option_contracts = []

                # Get the market data dataframe for call/put
                df_call, df_put = IndicatorHelper.get_mkt_data_df_for_call_and_put_options(
                    list_of_call_option_contracts, list_of_put_option_contracts, snapshot=False, generic_tick_list="101"
                )

                # from tabulate import tabulate

                # scanner_logger.info(
                #     f"Config ID: {self.config_id} Leg Number: {leg_number} Inside ScannerAlgo.filter_strikes, InstrumentID: {instrument_id} All Expiry in Range: {expiry_date_in_range}"
                # )

                # print("\n\n\n")
                # print(tabulate(df_call, headers="keys", tablefmt="psql", showindex=False))
                # print("\n\n\nPUT")
                # print(tabulate(df_put, headers="keys", tablefmt="psql", showindex=False))

                df_call["underlying_conid"] = underlying_conid
                df_put["underlying_conid"] = underlying_conid

                # todo early teminate
                if self.check_do_we_need_to_restart_scan() or self.check_do_we_need_to_skip_current_scan():
                    return []

                if right.upper() == "CALL":
                    key = ScannerAlgo.get_key_from_contract_for_scanner_algo(
                        symbol, expiry, sec_type, right, trading_class, multiplier, exchange
                    )
                    DataStore.store_data(key, df_call)
                    df = df_call.copy()
                elif right.upper() == "PUT":
                    key = ScannerAlgo.get_key_from_contract_for_scanner_algo(
                        symbol, expiry, sec_type, right, trading_class, multiplier, exchange
                    )
                    DataStore.store_data(key, df_put)
                    df = df_put.copy()

            df.dropna(subset=["Delta", "Bid", "Ask", "AskIV", "UnderlyingPrice"], inplace=True)

            if right.upper() == "PUT":
                df["Delta"] = df["Delta"].abs()

            # Make a copy of the dataframe to avoid modifying the original dataframe
            filtered_dataframe = df.copy()

            # Filter strikes based on delta_range_low and delta_range_high
            filtered_dataframe = filtered_dataframe[
                (filtered_dataframe["Delta"] >= delta_range_low) & (filtered_dataframe["Delta"] <= delta_range_high)
            ]

            list_of_filtered_legs_tuple.extend(
                list(
                    # "Strike", "Expiry", "Delta", "ConId",
                    filtered_dataframe[
                        [
                            "Symbol",
                            "Strike",
                            "Delta",
                            "ConId",
                            "Expiry",
                            "Bid",
                            "Ask",
                            "AskIV",
                            "underlying_conid",
                            "Vega",
                            "Theta",
                            "Gamma",
                            "UnderlyingPrice",
                        ]
                    ].itertuples(index=False, name=None)
                )
            )

        return list_of_filtered_legs_tuple

    @cache
    def generate_combinations(self, remaining_no_of_legs, range_low, range_high, current_expiry, leg_object):

        scanner_logger.debug(
            f"ScannerAlgo.generate_combinations, Config ID: {self.config_id} Inputs: {remaining_no_of_legs=} {range_low=} {range_high=} {current_expiry=} {leg_object=}"
        )
        # Get the list of filter legs between the given range for the expiry
        list_of_filter_legs = self.filter_strikes(range_low, range_high, current_expiry, remaining_no_of_legs, leg_object)
        # print(f"list of filter leg: {list_of_filter_legs}")
        scanner_logger.debug(
            f"ScannerAlgo.generate_combinations, Config ID: {self.config_id} No. of Filtered Legs: {len(list_of_filter_legs)}"
        )

        # Check early teminate
        if self.check_do_we_need_to_restart_scan() or self.check_do_we_need_to_skip_current_scan():
            return []

        list_of_partial_combination = []

        if remaining_no_of_legs == 0:
            for (
                symbol,
                strike,
                strike_delta,
                con_id,
                expiry,
                bid,
                ask,
                last_iv,
                underlying_conid,
                vega,
                theta,
                gamma,
                und_price,
            ) in list_of_filter_legs:
                list_of_partial_combination.append(
                    [(symbol, strike, strike_delta, con_id, expiry, bid, ask, last_iv, underlying_conid, vega, theta, gamma, und_price)]
                )
        else:
            # get the next leg object to scan
            list_of_config_leg_object = self.config_obj.list_of_config_leg_object
            leg_object = list_of_config_leg_object[-remaining_no_of_legs]
            (
                leg_number,
                _,
                action,
                _qty,
                _,
                delta_range_min,
                delta_range_max,
                _,
                _,
            ) = leg_object.get_config_leg_tuple_for_gui()

            delta_range_min = float(delta_range_min)
            delta_range_max = float(delta_range_max)

            for (
                symbol,
                strike,
                strike_delta,
                con_id,
                expiry,
                bid,
                ask,
                last_iv,
                underlying_conid,
                vega,
                theta,
                gamma,
                und_price,
            ) in list_of_filter_legs:

                new_range_low = strike_delta + delta_range_min
                new_range_high = strike_delta + delta_range_max
                expiry_date_obj = datetime.datetime.strptime(expiry, "%Y%m%d")

                list_of_strike_delta_and_con_id_tuple = self.generate_combinations(
                    remaining_no_of_legs - 1, new_range_low, new_range_high, expiry_date_obj, leg_object
                )

                current_leg_strike_and_strike_delta = [
                    (symbol, strike, strike_delta, con_id, expiry, bid, ask, last_iv, underlying_conid, vega, theta, gamma, und_price)
                ]

                for next_legs_strike_delta_and_con_id in list_of_strike_delta_and_con_id_tuple:

                    temp = current_leg_strike_and_strike_delta[:]
                    temp.extend(next_legs_strike_delta_and_con_id)
                    list_of_partial_combination.append(temp)

        return list_of_partial_combination

    def filter_list_of_combination(self, list_of_combination):
        """
        Combo:
        Leg 1: AAPL 20240419 C 100 +1,
        Leg 2: AAPL 20240419 C 100 -1,
        Leg 3: AAPL 20240419 C 110 +2,

        Net Combo => AAPL 20240419 C 110 +2
        So we will be ignoring all such combos.
        """

        temp_list_of_combination = []

        for combo in list_of_combination:
            temp_list_of_combination.append(tuple(combo))

        # (instrumnt, C/P, expiry, strike, )
        set_of_combination = set(temp_list_of_combination)

        # Get the list of config_leg object
        list_of_config_leg_object = self.config_obj.list_of_config_leg_object

        list_of_filter_combination = []

        for combination in set_of_combination:

            set_of_legs = set()

            for leg_tuple, leg_object in zip(combination, list_of_config_leg_object):
                # Extract the Strike, Expiry
                _, strike, delta, conid, expiry, _, _, _, _, _, _, _, _ = leg_tuple

                # Get the action and instrument id from leg object
                right = leg_object.right
                instrument_id = leg_object.instrument_id

                if (instrument_id, right, expiry, strike) in set_of_legs:
                    break

                # Add the unique instrument id expiry strike action
                set_of_legs.add((instrument_id, right, expiry, strike))
            else:
                list_of_filter_combination.append(combination)

        return list_of_filter_combination

    def remove_duplicate_combo_different_order(self, list_of_filter_combination):
        """
        Below cases are also ignored for duplicates
        Duplicate:
            AAPL 20240419 C 105 +1,  AAPL 20240419 C 110 +2,  AAPL 20240419 C 100 -1
            AAPL 20240419 C 110 +2,  AAPL 20240419 C 105 +1,  AAPL 20240419 C 100 -1
        """
        list_of_config_leg_object = self.config_obj.list_of_config_leg_object
        unique_filter_combination = []
        seen_combination = set()

        # Looping over list of filter_combonation
        for combination in list_of_filter_combination:

            # Temp Combintaion will be in new format, [(Leg1-Strike, Leg1-Action), (Leg2-Strike, Leg2-Action),...]
            temp_combination = []

            # Loop leg_tuple in combination and the leg_object in the list_of_config_leg_object
            for leg_tuple, leg_object in zip(combination, list_of_config_leg_object):

                # Get the leg number & action for the leg, from the respective leg_object
                leg_number = leg_object.leg_number
                action = leg_object.action
                qty = leg_object.quantity
                instrument_id = leg_object.instrument_id
                right = leg_object.right
                # Unpack the Strike Delta & Conid from a Leg:  (5100.0B, 0.6981448441368908, 0)
                _, strike, delta, conid, expiry, _, _, _, _, _, _, _, _ = leg_tuple

                # AAPL 20240419 C 100 +1, AAPL 20240419 C 110 +2, AAPL 20240419 C 100 -1

                temp_leg_tuple = (instrument_id, expiry, right, strike, action, qty)
                temp_combination.append(temp_leg_tuple)

            temp_combination = sorted(temp_combination)
            # Cast to Tuple: so combination can be hashed
            temp_combination = tuple(temp_combination)

            # if not in seen add sublist to uniique
            if temp_combination not in seen_combination:
                unique_filter_combination.append(combination)
                seen_combination.add(temp_combination)

        return unique_filter_combination

    def run_scanner(self, remaining_no_of_legs, range_low, range_high, current_date, leg_object):

        scanner_logger.info(f"ScannerAlgo.run_scanner, Config ID: {self.config_id} Generating Combos")

        list_of_combination = self.generate_combinations(
            remaining_no_of_legs,
            range_low,
            range_high,
            current_expiry=current_date,
            leg_object=leg_object,
        )

        scanner_logger.info(f"ScannerAlgo.run_scanner, Config ID: {self.config_id} No. of Generated Combos: {len(list_of_combination)}")

        # print("combination", list_of_combination)
        # print("list_of_combination", list_of_combination)
        list_of_filter_combination = self.filter_list_of_combination(list_of_combination)

        scanner_logger.info(f"ScannerAlgo.run_scanner, Config ID: {self.config_id} No. of Filtered Combos: {len(list_of_combination)}")

        list_of_filter_combination_without_dup = self.remove_duplicate_combo_different_order(list_of_filter_combination)

        scanner_logger.info(
            f"ScannerAlgo.run_scanner, Config ID: {self.config_id} No. of Unique Combos: {len(list_of_filter_combination_without_dup)}"
        )

        return list_of_filter_combination_without_dup

    def check_do_we_need_to_skip_current_scan(
        self,
    ):
        """
        True: Indicates skip the current scan (config)
        False: Indicates continue with  the current scan (config)
        """

        # If Config ID is None, please skip this scan
        if self.config_id is None:
            scanner_logger.info(f"Inside Scan Algo: Config ID: {self.config_id} do not exist skipping scan")
            return True
        # If Config got deleted, please skip this scan
        elif not self.config_id in StrategyVariables.map_config_id_to_config_object:
            scanner_logger.info(f"Inside Scan Algo: Config ID: {self.config_id} do not exist skipping scan")
            return True

        return False

    def check_do_we_need_to_restart_scan(
        self,
    ):
        """
        False: Indicates do not need to restart scan
        True: Indicates do need to restart scan
        """

        # User Clicked on Force Restart
        if StrategyVariables.flag_force_restart_scanner:
            scanner_logger.info(f"Inside Scan Algo: Config ID: {self.config_id} Scanned Combo, Force Restart")
            return True

        return False

    def update_indicator_table_for_instrument(
        self,
        instrument_object,
        set_of_all_closest_expiry,
        map_closest_expiry_to_underlying_conid,
        leg_number,
    ):
        """Updates the indicator table for a given instrument."""

        # Instrument ID
        instrument_id = instrument_object.instrument_id

        scanner_logger.info(
            f"      Config ID: {self.config_id}  Inside ScannerAlgo.update_indicator_table_for_instrument, InstrumentID: {instrument_id}, Set of Valid Expiry: {set_of_all_closest_expiry}"
        )

        c_time = int(time.time())

        # Get old rows such that, where unix time  < 10 min ago, config_id, leg_number, instument_id.
        where_condition = f" WHERE `unix_time` < {c_time  - (10 * 60)} AND `config_id` = {self.config_id} AND `instrument_id` = {instrument_id} AND `leg_number` = {leg_number};"

        select_query = SqlQueries.create_select_query(
            table_name="config_indicator_relation",
            columns="*",
            where_clause=where_condition,
        )

        # Get all the old rows from config_relation_table
        all_the_existing_rows_form_db_table = SqlQueries.execute_select_query(select_query)
        list_of_config_relation_tuple_for_deletion = [
            (row["config_id"], row["instrument_id"], row["expiry"]) for row in all_the_existing_rows_form_db_table
        ]

        scanner_logger.info(
            f"      Config ID: {self.config_id}  Inside ScannerAlgo.update_indicator_table_for_instrument, InstrumentID: {instrument_id}, List of Old Valid Deletion Tuple: {list_of_config_relation_tuple_for_deletion}"
        )

        # Getting the new current list of <ConfigID, InstrumentID, Expiry> from Scanner
        list_of_current_config_relation_tuple = []

        # Getting each expiry from set of closest expiry
        for expiry in set_of_all_closest_expiry:
            list_of_current_config_relation_tuple.append((self.config_id, leg_number, instrument_id, expiry))

        scanner_logger.info(
            f"      Config ID: {self.config_id}  Inside ScannerAlgo.update_indicator_table_for_instrument, InstrumentID: {instrument_id}, List of Current Valid ConfigIndicatorRelation Tuple: {list_of_current_config_relation_tuple}"
        )

        # Insert all the insertion list in the config_relation table
        for config_id, leg_number, instrument_id, expiry in list_of_current_config_relation_tuple:
            config_indicator_relation_dict = {
                "config_id": config_id,
                "leg_number": leg_number,
                "instrument_id": instrument_id,
                "expiry": expiry,
                "unix_time": c_time,
            }
            res = self.insert_row_in_config_indicator_relation_db(values_dict=config_indicator_relation_dict)
            scanner_logger.info(
                f"      Config ID: {self.config_id}  Inside ScannerAlgo.update_indicator_table_for_instrument, InstrumentID: {instrument_id}, Insertion Result: {res} <{config_id, instrument_id, expiry}> "
            )

        # Addition of Indicators in Indicator Table from insertion list
        for config_id, leg_number, instrument_id, expiry in list_of_current_config_relation_tuple:
            underlying_conid = map_closest_expiry_to_underlying_conid[int(expiry)]

            # Query to get the count of rows
            where_condition = f" WHERE `instrument_id` = {instrument_id} AND `expiry` = {expiry};"
            select_query = SqlQueries.create_select_query(
                table_name="config_indicator_relation",
                columns="Count(*)",
                where_clause=where_condition,
            )

            # Getting the Count of rows
            count_of_existing_row = SqlQueries.execute_select_query(select_query)
            count_row = count_of_existing_row[0]["Count(*)"]

            scanner_logger.info(
                f"      Config ID: {self.config_id}  Inside ScannerAlgo.update_indicator_table_for_instrument, InstrumentID: {instrument_id}, #Rows: {count_row} for <{instrument_id, expiry}> "
            )

            if count_row == 1:

                new_dict = {
                    "instrument_id": instrument_object.instrument_id,
                    "symbol": instrument_object.symbol,
                    "sec_type": instrument_object.sec_type,
                    "multiplier": instrument_object.multiplier,
                    "trading_class": instrument_object.trading_class,
                    "expiry": expiry,
                    "underlying_conid": underlying_conid,
                    "exchange": instrument_object.exchange,
                }
                self.insert_new_indicator_row_in_db_gui_and_system(new_dict)

        where_condition = f" WHERE `unix_time` < {c_time  - (10 * 60)} AND `config_id` = {self.config_id} AND `instrument_id` = {instrument_id} AND `leg_number` = {leg_number};"

        # Delet old rows where unix time  < 10 min ago, config_id, leg_number, instument_id
        delete_query = SqlQueries.create_delete_query(table_name="config_indicator_relation", where_clause=where_condition)
        res = SqlQueries.execute_delete_query(delete_query)
        if not res and list_of_config_relation_tuple_for_deletion:
            print(f"Error: Deletion not succesful for config_indicator_relation: {self.config_id}")

        Utils.deletion_indicator_rows_based_on_config_tuple_relation(list_of_config_relation_tuple_for_deletion)

