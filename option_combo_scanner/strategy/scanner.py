import asyncio
import copy
from com.contracts import get_contract, get_contract_details
from com.greeks import async_get_deltas
from com.leg_identifier import (
    find_closest_expiry_for_fop_given_fut_expiries_and_trading_class,
    find_nearest_expiry_and_all_strikes_for_stk_given_dte,
    find_nearest_expiry_for_future_given_fut_dte,
)
from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.strategy.scanner_combination import ScannerCombination
from option_combo_scanner.strategy.scanner_leg import ScannerLeg
from option_combo_scanner.strategy.strategy_variables import StrategyVariables
from tabulate import tabulate
import pandas as pd
from option_combo_scanner.strategy.scanner_algo import ScannerAlgo


class Scanner:
    x = f"Scanner Class: scanner_combination_tab_obj".upper()
    print(x)

    scanner_combination_tab_obj = None
    
    def __init__(self,):
        pass

    """
    Instrument: AAPL, STK, SMART
    DTE: 7

    Get Instrument and, Config [strategy_variable]
    base/underlying:
        contrac deatils
        contract
    """

    def get_strike_and_closet_expiry_for_fop(
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
            return None, None

        # get closest FOP Expiry for given Trading class
        (
            all_strikes,
            closest_expiry_date,
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

        return all_strikes, closest_expiry_date

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
        all_expiry_dates_ticker, string_of_strike_price, closest_expiry_date = (
            find_nearest_expiry_and_all_strikes_for_stk_given_dte(
                ticker=symbol,
                days_to_expiry=dte,
                underlying_sec_type=underlying_sec_type,
                exchange=exchange,
                currency=currency,
                multiplier=multiplier,
                fop_trading_class="",
            )
        )
        return string_of_strike_price, closest_expiry_date

    def get_instrument_from_variables(
        self,
    ):
        local_map_instrument_id_to_instrument_object = copy.deepcopy(
            StrategyVariables.map_instrument_id_to_instrument_object
        )
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

    def start_scanner(
        self,
    ):
        
        local_map_instrument_id_to_instrument_object = (
            self.get_instrument_from_variables()
        )
        local_config_object = self.get_config_from_variables()

        for (
            instrument_id,
            instrument_object,
        ) in local_map_instrument_id_to_instrument_object.items():
            symbol = instrument_object.symbol
            sec_type = instrument_object.sec_type
            multiplier = instrument_object.multiplier
            exchange = instrument_object.exchange
            trading_class = instrument_object.trading_class
            currency = instrument_object.currency
            conid = instrument_object.conid
            primary_exchange = instrument_object.primary_exchange

            # TODO - Karan
            # Get incomplete underlying contract
            # underlying_contract = self.get_contract_from_instrument_object(
            #     instrument_object
            # )
            # list_of_contracts = [underlying_contract]

            # # Complete contarct for conid
            # list_of_complete_contracts = self.get_list_contract_details(
            #     list_of_contracts=list_of_contracts
            # )
            
            try:
                right = local_config_object.right
                        
                list_of_dte_string_form = local_config_object.list_of_dte
                        
                list_of_dte = [int(num) for num in list_of_dte_string_form.split(",")]

            except AttributeError:
                # Handle the case where local_config_object does not have the expected attributes
                print(f"Add Configuration Values")
                # print("Error: local_config_object does not have the expected attributes.")
                
                right = None
                list_of_dte = []

            
            # print("list of dte", list_of_dte)
            
            # Based on sec_type wil run the scan for instrument
            if sec_type == "OPT":
                self.run_scan_for_opt(
                    config_obj=local_config_object,
                    instrument_object=instrument_object,
                    list_of_dte=list_of_dte,
                    right=right,
                )
            elif sec_type == "FOP":
                self.run_scan_for_fop(
                    config_obj=local_config_object,
                    instrument_object=instrument_object,
                    list_of_dte=list_of_dte,
                    right=right,
                )
            else:
                print(f"Security Type {sec_type} is invalid for {instrument_object}")
                continue

    def run_scan_for_opt(self, config_obj, instrument_object, list_of_dte, right):
        symbol = instrument_object.symbol
        sec_type = instrument_object.sec_type
        multiplier = instrument_object.multiplier
        exchange = instrument_object.exchange
        trading_class = instrument_object.trading_class
        currency = instrument_object.currency
        conid = instrument_object.conid
        primary_exchange = instrument_object.primary_exchange

        set_of_all_closest_expiry = set()
        all_strikes = None

        for dte in list_of_dte:

            # OPT/FOP
            # Get all the expiry from the list of DTE
            all_strikes_string, closest_expiry = (
                self.get_strike_and_closet_expiry_for_opt(
                    symbol=symbol,
                    dte=dte,
                    underlying_sec_type="STK",
                    exchange=exchange,
                    currency=currency,
                    multiplier=multiplier,
                    trading_class="",
                )
            )
            if all_strikes_string == None or closest_expiry == None:
                continue

            set_of_all_closest_expiry.add(closest_expiry)

            # Removing  {  }
            all_strikes = [float(_) for _ in all_strikes_string[1:-1].split(",")]

            all_strikes = sorted(all_strikes)

        
        for expiry in set_of_all_closest_expiry:
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
                        trading_class=None,
                    )
                )

            list_of_all_option_delta = asyncio.run(
                async_get_deltas(
                    contracts_list=list_of_all_option_contracts, flag_market_open=True
                )
            )

            columns = ["Strike", "Delta", "ConId"]
            data_frame_dict = { col: [] for col in columns}            
            for contract, delta in zip(
                list_of_all_option_contracts, list_of_all_option_delta
            ):
                data_frame_dict["Strike"].append(contract.strike)
                data_frame_dict["Delta"].append(str(delta))
                data_frame_dict["ConId"].append(contract.conId)

            df = pd.DataFrame(data_frame_dict)
            # print(df)
            print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))

            list_of_all_generated_combination = self.generate_combinations(
                config_obj=config_obj,
                instrument_object=instrument_object,
                strike_and_delta_dataframe=df,
            )
            list_of_combo_net_deltas = self.get_list_combo_net_delta(config_obj=config_obj,
                                     list_of_all_generated_combination=list_of_all_generated_combination)
            self.insert_combinations_into_db(list_of_all_generated_combination, instrument_object, list_of_combo_net_deltas)

    def run_scan_for_fop(self, config_obj, instrument_object, list_of_dte, right):
        symbol = instrument_object.symbol
        sec_type = instrument_object.sec_type
        multiplier = instrument_object.multiplier
        exchange = instrument_object.exchange
        trading_class = instrument_object.trading_class
        currency = instrument_object.currency
        conid = instrument_object.conid
        primary_exchange = instrument_object.primary_exchange

        set_of_all_closest_expiry = set()
        all_strikes = None

        for dte in list_of_dte:

            # OPT/FOP
            # Get all the expiry from the list of DTE
            all_strikes, closest_expiry = self.get_strike_and_closet_expiry_for_fop(
                symbol=symbol,
                dte=dte,
                underlying_sec_type="FUT",
                exchange=exchange,
                currency=currency,
                multiplier=multiplier,
                trading_class=trading_class,
            )
            if all_strikes is None or closest_expiry == None:
                continue

            set_of_all_closest_expiry.add(closest_expiry)
       
        for expiry in set_of_all_closest_expiry:
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

            list_of_all_option_delta = asyncio.run(
                async_get_deltas(
                    contracts_list=list_of_all_option_contracts, flag_market_open=True
                )
            )
            

            columns = ["Strike", "Delta", "ConId"]
            data_frame_dict = { col: [] for col in columns}
            for contract, delta in zip(
                list_of_all_option_contracts, list_of_all_option_delta
            ):
                data_frame_dict["Strike"].append(contract.strike)
                data_frame_dict["Delta"].append(str(delta))
                data_frame_dict["ConId"].append(contract.conId)

            df = pd.DataFrame(data_frame_dict)
            # print(df)
            print(tabulate(df, headers="keys", tablefmt="psql", showindex=False))

            list_of_all_generated_combination = self.generate_combinations(
                    config_obj=config_obj,
                    instrument_object=instrument_object,
                    strike_and_delta_dataframe=df,

                )
            # Get the list of net combo delta for the list of combinations
            list_of_combo_net_deltas = self.get_list_combo_net_delta(config_obj=config_obj,
                                     list_of_all_generated_combination=list_of_all_generated_combination)
            
            self.insert_combinations_into_db(list_of_all_generated_combination, instrument_object, expiry, list_of_combo_net_deltas)

    def generate_combinations(
        self, config_obj, instrument_object, strike_and_delta_dataframe
    ):

        # Get the configurations
        remaining_no_of_legs = config_obj.no_of_leg - 1
        range_low = config_obj.list_of_config_leg_object[0].delta_range_min
        range_high = config_obj.list_of_config_leg_object[0].delta_range_max

        # List
        res = ScannerAlgo(config_obj=config_obj, strike_and_delta_dataframe=strike_and_delta_dataframe).run_scanner(
            remaining_no_of_legs,
            range_low,
            range_high,
        )
        
        # print("---", res)
        return res
        
    def insert_combinations_into_db(self, list_of_all_generated_combination, instrument_object, expiry, list_of_combo_net_deltas):
        
        config_obj = self.get_config_from_variables()
        list_of_config_leg_object = config_obj.list_of_config_leg_object

        values_dict = {
            'instrument_id': instrument_object.instrument_id,
            'number_of_legs': config_obj.no_of_leg,
            'symbol': instrument_object.symbol,
            'sec_type': instrument_object.sec_type,
            'expiry': expiry,
            'right': config_obj.right,
            'multiplier': instrument_object.multiplier,
            'trading_class': instrument_object.trading_class,
            'currency': instrument_object.currency,
            'exchange': instrument_object.exchange,
        }
            
        for combination, combo_net_delta in zip(list_of_all_generated_combination, list_of_combo_net_deltas):
            
            # Remove the key, val if exists form prev iter
            if 'combo_id' in values_dict:
                del values_dict['combo_id']
            # Remove the key, val if exists form prev iter
            if 'list_of_all_leg_objects' in values_dict:
                del values_dict['list_of_all_leg_objects']
            
            values_dict['combo_net_delta'] = combo_net_delta
            res, combo_id = SqlQueries.insert_into_db_table(table_name="combination_table", values_dict=values_dict)
            if not res:
                print(f"Unable to insert Combination in the table: {combination}")
                continue
                
            # list of leg object
            list_of_all_leg_objects = []
            for index, ((strike,delta,con_id), config_leg_object) in enumerate(zip(combination, list_of_config_leg_object)):
                leg_values_dict = {
                'combo_id': combo_id,
                'leg_number': index + 1,
                'con_id': con_id,
                'strike': strike,
                'qty': 1,
                'delta_found':delta,
                'action': config_leg_object.action,
                'delta_range_min':config_leg_object.delta_range_min,
                'delta_range_max':config_leg_object.delta_range_max,
                }
                res, leg_id = SqlQueries.insert_into_db_table(table_name="legs_table", values_dict=leg_values_dict)
                if not res:
                    print(f"Unable to insert leg in the table: {leg_values_dict}")

                list_of_all_leg_objects.append(ScannerLeg(leg_values_dict))

            # Add the combo_id and leg objects
            values_dict['combo_id'] = combo_id
            values_dict['list_of_all_leg_objects'] = list_of_all_leg_objects
            
            # Scanner Combination Object
            scanner_combination_object = ScannerCombination(values_dict)
            
            # Insert the Scanner combination in GUI
            Scanner.scanner_combination_tab_obj.insert_combination_in_scanner_combination_table_gui(scanner_combination_object)
            
    # Calulation of Combo Net Delta
    def get_list_combo_net_delta(self, config_obj, list_of_all_generated_combination):
        list_of_config_leg_object = config_obj.list_of_config_leg_object
        list_of_combo_net_deltas= []
        # Loop over list of combination
        for combination in list_of_all_generated_combination:
            net_combo = 0
            # Loop over leg object to get action for the leg
            for leg_tuple, leg_object in zip(combination, list_of_config_leg_object):
                action = leg_object.action
                _, delta, _ = leg_tuple
                # if Buy will add the delta
                if action == 'Buy':
                    net_combo += delta
                # If Sell will substract the delta
                else:
                    net_combo -= delta
            net_combo = f"{float(net_combo):,.4f}"
            list_of_combo_net_deltas.append(net_combo)    
        return list_of_combo_net_deltas    
