import asyncio
import copy
import datetime
from functools import cache
import pandas as pd

from com.contracts import get_contract
from com.option_comobo_scanner_idetif import find_closest_expiry_for_fop_given_fut_expiries_and_trading_class, find_nearest_expiry_and_all_strikes_for_stk_given_dte, find_nearest_expiry_for_future_given_fut_dte
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.indicators_calculator.market_data_fetcher import MarketDataFetcher
from option_combo_scanner.strategy.indicator import Indicator
from option_combo_scanner.strategy.strategy_variables import StrategyVariables


class ScannerAlgo:

    # def __init__(self):
    def __init__(self, config_obj):
        self.config_obj = config_obj
        # self.strike_and_delta_dataframe = strike_and_delta_dataframe

        # Filter the nan Values
        # self.filter_dataframe()

    def get_strike_and_closet_expiry_for_fop(
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
        and closest expiry for FOP sec_type

        """

        # print(
        #     "Scanner: ",
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
    #         self.insert_new_indicator_row_in_db_gui_and_system(new_dict)

    # def insert_new_indicator_row_in_db_gui_and_system(self, values_dict):

    #     res, indicator_id = SqlQueries.insert_into_db_table(table_name="indicator_table", values_dict=values_dict)
    #     if not res:
    #         return
    #     values_dict["indicator_id"] = indicator_id
    #     indicator_obj = Indicator(values_dict)

    #     # Insertion of indicator data in GUI
    #     Scanner.scanner_indicator_tab_obj.insert_into_indicator_table(indicator_obj)

    
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
            fop_trading_class="",
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
        self.strike_and_delta_dataframe = self.strike_and_delta_dataframe.replace(
            "None", float("nan")
        )

        # Convert values to float
        self.strike_and_delta_dataframe = self.strike_and_delta_dataframe.apply(
            pd.to_numeric, errors="coerce"
        )

        # Converting Delta values to absolute
        self.strike_and_delta_dataframe["Delta"] = self.strike_and_delta_dataframe[
            "Delta"
        ].abs()

        # Remove all the row that have delta less than min_delta_threshold
        if StrategyVariables.flag_enable_filter_based_delta_threshold:
            self.strike_and_delta_dataframe = self.strike_and_delta_dataframe[
                (
                    self.strike_and_delta_dataframe["Delta"]
                    > StrategyVariables.min_delta_threshold
                )
            ]

            # Remove all the row that have delta higher than max_delta_threshold
            self.strike_and_delta_dataframe = self.strike_and_delta_dataframe[
                (
                    self.strike_and_delta_dataframe["Delta"]
                    < StrategyVariables.max_delta_threshold
                )
            ]

        # print("\nFiltered DF")
        # from tabulate import tabulate
        # print(tabulate(self.strike_and_delta_dataframe, headers="keys", tablefmt="psql", showindex=False))

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
        print(delta_range_low, delta_range_high, current_expiry)

        # If we can get all the valid strikes over all the valid expiries for the leg, then we are good. 
        # list_of_filter_legs = self.filter_strikes(range_low, range_high,) # ConfigLeg, Expiry of the perivous leg N-1 Leg,
        instrument_id = leg_object.instrument_id
        minDTE = leg_object.dte_range_min
        maxDTE = leg_object.dte_range_max
        right = leg_object.right
        instrument_object = copy.deepcopy(StrategyVariables.map_instrument_id_to_instrument_object[instrument_id])
        symbol = instrument_object.symbol

        sec_type = instrument_object.sec_type
        multiplier = instrument_object.multiplier
        exchange = instrument_object.exchange
        trading_class = instrument_object.trading_class
        currency = instrument_object.currency    
        set_of_all_closest_expiry = set()
        all_strikes = None
        res_list_of_filtered_df = []
        map_closest_expiry_to_underlying_conid = {}
        low_range_date_str = (current_expiry - datetime.timedelta(days=minDTE)).strftime("%Y%m%d") 
        high_range_date_str = (current_expiry + datetime.timedelta(days=maxDTE)).strftime("%Y%m%d")
        
        if sec_type == 'FOP':
            
            (all_strikes, closest_expiry, underlying_conid, expiry_date_in_range) = self.get_strike_and_closet_expiry_for_fop(
                                                        symbol=symbol,
                                                        dte=1,
                                                        underlying_sec_type="FUT",
                                                        exchange=exchange,
                                                        currency=currency,
                                                        multiplier=multiplier,
                                                        trading_class=trading_class,
                                                        low_range_date_str=low_range_date_str,
                                                        high_range_date_str=high_range_date_str,
                                                        
                                                    )
            # if all_strikes is None or closest_expiry == None:
            #     continue
        elif sec_type == 'OPT':
            (
                all_strikes_string,
                closest_expiry,
                underlying_conid,
                expiry_date_in_range,
            ) = self.get_strike_and_closet_expiry_for_opt(
                symbol=symbol,
                dte=1,
                underlying_sec_type="STK",
                exchange=exchange,
                currency=currency,
                multiplier=multiplier,
                trading_class="",
                low_range_date_str=low_range_date_str,
                high_range_date_str=high_range_date_str,
            )
            all_strikes = [float(_) for _ in all_strikes_string[1:-1].split(",")]

            all_strikes = sorted(all_strikes)
            # map_closest_expiry_to_underlying_conid[int(closest_expiry)] = underlying_conid
        #     self.update_indicator_table_for_instrument(
        #     instrument_object,
        #     expiry_date_in_range,
        #     map_closest_expiry_to_underlying_conid,
        # )
        print(expiry_date_in_range)
        for expiry in expiry_date_in_range:
        # print("All Strike: ", all_strikes)

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
        
    # Fetch Data for all the  Contracts
        list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_tuple = asyncio.run(
            MarketDataFetcher.get_option_delta_and_implied_volatility_for_contracts_list_async(
                list_of_all_option_contracts,
                flag_market_open=False,
                generic_tick_list="",
            )
        )

        # pprint.pprint(list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_tuple)

        columns = [
            "Strike",
            "Delta",
            "ConId",
            "Bid",
            "Ask",
            "Expiry",
        ]
        data_frame_dict = {col: [] for col in columns}

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
            list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_tuple,
        ):
            data_frame_dict["Strike"].append(contract.strike)
            data_frame_dict["Delta"].append((delta))
            data_frame_dict["ConId"].append(contract.conId)

            data_frame_dict["Bid"].append(bid_price)
            data_frame_dict["Ask"].append(ask_price)
            data_frame_dict["Expiry"].append(contract.lastTradeDateOrContractMonth)

        df = pd.DataFrame(data_frame_dict)

        df.dropna(inplace=True)

    # 1. Get all the expries for the instrument
    # Current Date: MinDTE, MaxDTE: 7:  7  14  -> 14, expiry 21
    # Leg1: <7,14> March 15 Leg2: MinDTE=-2, MaxDte=2<13,17>
    # Filter all the valid strikes. 
    # Get MktData for all the Expiry  

    # Make a copy of the dataframe to avoid modifying the original dataframe
        filtered_dataframe = df.copy()

    # Filter strikes based on delta_range_low and delta_range_high
        filtered_dataframe = filtered_dataframe[
                (filtered_dataframe["Delta"] >= delta_range_low)
                & (filtered_dataframe["Delta"] <= delta_range_high)
            ]


    
        res_list_of_filtered_df.extend(list(
                # "Strike", "Expiry", "Delta", "ConId", 
                filtered_dataframe[["Strike", "Delta", "ConId", "Expiry"]].itertuples(
                    index=False, name=None
                )
            ))
        return res_list_of_filtered_df


    @cache
    def generate_combinations(self, remaining_no_of_legs, range_low, range_high, current_expiry, leg_object):
        # If we can get all the valid strikes over all the valid expiries for the leg, then we are good. Leg0: Leg1 Leg2
        list_of_filter_legs = self.filter_strikes(range_low, range_high, current_expiry, remaining_no_of_legs, leg_object) # current_expiry, ConfigLeg, Expiry of the perivous leg N-1 Leg: Current Date
        # ("Strike", "Expiry", "Delta", "ConId"), 
        print(f"list of filter leg: {list_of_filter_legs}")
        list_of_partial_combination = []

        if remaining_no_of_legs == 0:
            for strike, strike_delta, con_id, expiry in list_of_filter_legs:
                list_of_partial_combination.append([(strike, strike_delta, con_id, expiry)])
        else:
            list_of_config_leg_object = self.config_obj.list_of_config_leg_object
            leg_object = list_of_config_leg_object[-remaining_no_of_legs]

            (
                leg_number,
                _,
                action,
                _,
                delta_range_min,
                delta_range_max,
                _,
                _,
            ) = leg_object.get_config_leg_tuple_for_gui()

            delta_range_min = float(delta_range_min)
            delta_range_max = float(delta_range_max)

            for strike, strike_delta, con_id, expiry in list_of_filter_legs:

                new_range_low = strike_delta + delta_range_min
                new_range_high = strike_delta + delta_range_max
                expiry_date_obj = datetime.datetime.strptime(expiry, "%Y%m%d")
                print("leg object recursion", leg_object)
                list_of_strike_delta_and_con_id_tuple = self.generate_combinations(
                    remaining_no_of_legs - 1,
                    new_range_low,
                    new_range_high,
                    expiry_date_obj,
                    leg_object
                    
                )
                current_leg_strike_and_strike_delta = [(strike, strike_delta, con_id, expiry)]
                for (
                    next_legs_strike_delta_and_con_id
                ) in list_of_strike_delta_and_con_id_tuple:
                    temp = current_leg_strike_and_strike_delta[:]
                    temp.extend(next_legs_strike_delta_and_con_id)
                    list_of_partial_combination.append(temp)

        # print(f"remaining_no_of_legs {remaining_no_of_legs} list_of_partial_combination", list_of_partial_combination)
        return list_of_partial_combination

    def filter_list_of_combination(self, list_of_combination):

        temp_list_of_combination = []
        for combo in list_of_combination:
            temp_list_of_combination.append(tuple(combo))

            # temp_list_of_combination.append(tuple([strike for strike, delta in combo]))

        set_of_combination = set(temp_list_of_combination)

        list_of_filter_combination = []
        for combination in set_of_combination:
            set_of_legs = set()
            for leg in combination:
                strike = leg
                if strike in set_of_legs:
                    break
                set_of_legs.add(strike)
            else:
                list_of_filter_combination.append(combination)

        return list_of_filter_combination

    def remove_duplicate_combo_different_order(self, list_of_filter_combination):

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
                # Unpack the Strike Delta & Conid from a Leg:  (5100.0B, 0.6981448441368908, 0)
                strike, delta, conid = leg_tuple

                temp_leg_tuple = (strike, action)
                temp_combination.append(temp_leg_tuple)

            # Cast to Tuple: so combination can be hashed
            temp_combination = tuple(temp_combination)

            # if not in seen add sublist to uniique
            if temp_combination not in seen_combination:
                unique_filter_combination.append(combination)
                seen_combination.add(temp_combination)

        return unique_filter_combination

    def run_scanner(
        self,
        remaining_no_of_legs,
        range_low,
        range_high,
        current_date,
        leg_object
    ):

        list_of_combination = self.generate_combinations(
            remaining_no_of_legs,
            range_low,
            range_high,
            current_expiry=current_date,
            leg_object = leg_object,
        )
        print("combination", list_of_combination)
        # print("list_of_combination", list_of_combination)
        # list_of_filter_combination = self.filter_list_of_combination(
        #     list_of_combination
        # )
        # list_of_filter_combination_without_dup = (
        #     self.remove_duplicate_combo_different_order(list_of_filter_combination)
        # )

        return list_of_combination
