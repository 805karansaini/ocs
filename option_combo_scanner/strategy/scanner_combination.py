import asyncio
import copy
from pprint import pprint
import warnings

import pandas as pd

from com.contracts import get_contract
from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.indicators_calculator.market_data_fetcher import \
    MarketDataFetcher
from option_combo_scanner.strategy.max_loss_profit_calculation import MaxPNLCalculation
from option_combo_scanner.strategy.strategy_variables import \
    StrategyVariables as strategy_variables

logger = CustomLogger.logger


class ScannerCombination:
    def __init__(
        self,
        values_dict,
    ):
        [setattr(self, key, value) for key, value in values_dict.items()]

        # Cast to integers
        self.combo_id = int(self.combo_id)
        # self.instrument_id = int(self.instrument_id)

        # Case to inf
        try:
            self.max_loss = float("-inf") if "inf" in self.max_loss else int(float(self.max_loss))
        except Exception as e:
            pass
            # print(f"Error for COmbo ID: ", self.combo_id, "max_loss", self.max_loss)

        try:
            self.max_profit = float("inf") if "inf" in self.max_profit else int(float(self.max_profit))
        except Exception as e:
            pass

            # print(f"Error for COmbo ID: ", self.combo_id, "max_profit", self.max_profit)

        # Set the combination description
        self.description = self.get_combo_description()

        # Map combination_id to combination object
        self.map_combo_id_to_scanner_combination_object()

    def map_combo_id_to_scanner_combination_object(self):

        strategy_variables.map_combo_id_to_scanner_combination_object[self.combo_id] = self

        # Create a new row data based on the retrieved values
        row = pd.DataFrame(
            {
                "Combo ID": self.combo_id,
                # "Instrument ID": self.instrument_id,
                "Description": self.description,
                "#Legs": self.number_of_legs,
                "Combo Net Delta": self.combo_net_delta,
                "Max Profit": self.max_profit,
                "Max Loss": self.max_loss,
                # "Max Profit/Loss Ratio": self.max_profit_max_loss_ratio,
            },
            index=[0],
        )

        # Add Row to dataframe (concat)
        warnings.filterwarnings("ignore", message="The behavior of DataFrame concatenation with empty or all-NA entries is deprecated.*")
        strategy_variables.scanner_combo_table_df = pd.concat(
            [strategy_variables.scanner_combo_table_df, row],
            ignore_index=True,
        )

    def remove_scanned_combo_from_system(self):

        # Remove row from dataframe
        # TODO Check
        strategy_variables.scanner_combo_table_df = strategy_variables.scanner_combo_table_df.drop(
            strategy_variables.scanner_combo_table_df[strategy_variables.scanner_combo_table_df["Combo ID"] == self.combo_id].index
        )

        del strategy_variables.map_combo_id_to_scanner_combination_object[self.combo_id]

    def __str__(self) -> str:

        return f"Scanner Combination Object: {pprint(vars(self))}"
    
    def get_combo_description(
        self,
    ):

        # Ticker 1 (Sec Type 1: Expiry 1 C/P Strike 1) +/- Qty 1,
        # Tickers Informative string
        combo_desc_string = ""

        # Processing Leg Obj and appending to combo_desc_string
        for leg_no, leg_obj in enumerate(self.list_of_all_leg_objects):

            # Symbol and SecType
            combo_desc_string += f"{leg_obj.symbol} ({leg_obj.sec_type}"

            # Expiry Date, Right, Strike
            combo_desc_string += f" {leg_obj.expiry} {leg_obj.right} {leg_obj.strike}"

            # Buy/Sell +1 or -1
            if leg_obj.action.upper() == "BUY":
                # check if it is last leg
                if leg_no == len(self.list_of_all_leg_objects) - 1:
                    combo_desc_string += f") +{leg_obj.qty}"
                else:
                    combo_desc_string += f") +{leg_obj.qty}, "
            else:
                # check if it is last leg
                if leg_no == len(self.list_of_all_leg_objects) - 1:
                    combo_desc_string += f") -{leg_obj.qty}"
                else:
                    combo_desc_string += f") -{leg_obj.qty}, "

        return combo_desc_string
    
    def get_scanner_combination_tuple_for_gui(
        self,
    ):
        """ """
        # Create a tuple with object attributes in the specified order
        combination_tuple = (
            self.combo_id,
            self.instrument_id,
            self.number_of_legs,
            self.symbol,
            self.sec_type,
            self.expiry,
            self.right,
            self.multiplier,
            self.trading_class,
            self.currency,
            self.exchange,
            self.combo_net_delta,
            self.max_profit,
            self.max_loss,
            self.max_profit_max_loss_ratio,
            self.list_of_all_leg_objects,
        )

        return combination_tuple
    
    def dispaly_combination_impact(self,):

        # Getitng the CombinationObj, ComboID, List of ComboLegObj
        combo_obj = self
        combo_id = combo_obj.combo_id
        list_of_combo_leg_object = combo_obj.list_of_all_leg_objects

        # Config ID, Confg Object, ListOfConfigLegObj
        config_id = combo_obj.config_id
        config_obj = copy.deepcopy(strategy_variables.config_object)
        list_of_config_leg_object = config_obj.list_of_config_leg_object
        

        # Creating the list_of_combo_leg_tuples_with_config_leg
        list_of_combo_leg_tuples_with_config_leg = []

        # Adding the config_leg_obj to the leg_tuple
        for combo_leg_object, config_leg_obj in zip(list_of_combo_leg_object, list_of_config_leg_object):
            temp_list = [combo_leg_object.symbol, combo_leg_object.strike, None, None, combo_leg_object.expiry, None, None, None, combo_leg_object.underlying_conid, config_leg_obj]
            list_of_combo_leg_tuples_with_config_leg.append(tuple(temp_list))
        
        # Creating the Groups Based on the Underlying
        map_underlying_conid_to_list_of_combination_group: dict = MaxPNLCalculation.create_group_same_und(list_of_combo_leg_tuples_with_config_leg, flag_return_dict=True)
        list_of_combination_groups = list(map_underlying_conid_to_list_of_combination_group.values())

        # Get the list of closest expiry for the groups
        list_of_closest_expiry_for_each_group = MaxPNLCalculation.find_closest_expiry_for_groups(list_of_combination_groups,)
        cl = min(list_of_closest_expiry_for_each_group)
        # 1.a We want to get the Current Price of Underlying Contract.
        # 1.b We want to get the Current Market Data for Option Contracts.
        # 1.c if required data is not available, throw an error popup.
        # 2. Manupulate the leg tuples, meaning update the None to fetched values 
        # 3. Impact
        
        # List of underlying contracts
        list_of_underlying_contract = []

        # Underlying Contracts 
        for underlying_conid, combination_group in map_underlying_conid_to_list_of_combination_group.items():
            
            # Unpacking the first leg
            symbol, _, _, _, _, _, _, _, underlying_conid, config_leg_obj = combination_group[0]

            # Get the Instrument SecType
            _instrument_id = config_leg_obj.instrument_id

            if _instrument_id not in strategy_variables.map_instrument_id_to_instrument_object:
                Utils.display_message_popup(
                    "Error",
                f"Can not compute the Impact: Unable to find Instrument ID: {_instrument_id}",
                )
                return
            # Get the instrument object details for contract creation
            instrument_obj_ = copy.deepcopy(strategy_variables.map_instrument_id_to_instrument_object[_instrument_id])
            sec_type_  = instrument_obj_.sec_type
            exchange_ = instrument_obj_.exchange
            currency_  = instrument_obj_.currency
            und_multiplier_  = instrument_obj_.multiplier
            if sec_type_ == "OPT":
                underlying_sec_type = "STK"
                underlying_multiplier = 1
                underlying_contract = get_contract(
                    symbol=symbol,
                    sec_type=underlying_sec_type,
                    exchange=exchange_,
                    currency=currency_,
                    multiplier=und_multiplier_,
                    con_id=underlying_conid,
                )
                list_of_underlying_contract.append(underlying_contract)
            else:
                underlying_sec_type = "FUT"
                underlying_multiplier = int(und_multiplier_)
                underlying_contract = get_contract(
                    symbol=symbol,
                    sec_type=underlying_sec_type,
                    exchange=exchange_,
                    currency=currency_,
                    multiplier=underlying_multiplier,
                    con_id=underlying_conid,
                )
                list_of_underlying_contract.append(underlying_contract)
        

    
        # Option Contracts
        # Creation of Option Contract
        list_of_leg_objects = self.list_of_all_leg_objects
        list_of_leg_strike_action_qty_tuple = [(leg_obj.symbol, leg_obj.strike, leg_obj.expiry, leg_obj.right, leg_obj.sec_type, leg_obj.multiplier, leg_obj.trading_class, leg_obj.exchange, leg_obj.currency) for leg_obj in list_of_leg_objects]
        list_of_option_contracts = []

        # Loop through each leg's strike, action, quantity, expiry, right, and multiplier and create option contracts, then add to the list
        for symbol,strike, expiry, right_, sec_type, multiplier_, trading_class_, exchange, currency in list_of_leg_strike_action_qty_tuple:
            option_contract = get_contract(
                symbol,
                sec_type,
                exchange,
                currency,
                expiry,
                strike,
                right_,
                multiplier_,
                trading_class=trading_class_,
            )
            list_of_option_contracts.append(option_contract)

        # Merged in list of both underlying and option contract
        list_underlying_and_option_contract = list_of_underlying_contract + list_of_option_contracts
        generic_tick_list = "101"
        snapshot = True
        flag_market_open=False
        max_wait_time = 9
        list_of_bid_ask_iv_tuple = asyncio.run(
            MarketDataFetcher.get_option_delta_and_implied_volatility_for_contracts_list_async(list_underlying_and_option_contract, flag_market_open, generic_tick_list, snapshot,max_wait_time)
        )



        # Get the Mkt Data  [ <Bid, Ask > | <Bid, Ask IV,> ], delta, iv, oi
        # list_of_: 
        # Validate if required values values are present or not.
    
        list_of_ba_mid = []
        for contract, (delta,iv_ask,iv_bid,iv_last,bid_price,ask_price,call_oi,put_oi,) in zip(list_underlying_and_option_contract[:2],list_of_bid_ask_iv_tuple[:2],):
            if bid_price is None or ask_price is None:
                print(f"bid_price or ask_price is None for contract: {contract}")
                return

            ba_mid = (bid_price + ask_price) / 2
            list_of_ba_mid.append(ba_mid)
        
        res = []
        title = f"Impact of Combo, Combo ID : {combo_id}"
        list_of_impact_percent = strategy_variables.list_of_percent_for_impact_calcluation
        impact_value_groups = [
            cl,
        ]
        # For each underlying and group calcluate the impact
        for (underlying_price), und_combination_group in zip(list_of_ba_mid, list_of_combination_groups):
            group_res = []
            # Loop over the list of impact percent
            for impact_per in list_of_impact_percent:
                underlying_strike_price = (underlying_price * (100 + impact_per)) / 100
                # Get the combination payoff 
                combination_payoff = MaxPNLCalculation.get_combination_payoff(
                    list_of_legs_tuple=und_combination_group,
                    list_of_config_leg_objects=list_of_combo_leg_tuples_with_config_leg,
                    underlying_strike_price = underlying_strike_price,
                    closest_expiry=cl,
                    multiplier=multiplier,
                )
                # Store the groupwise combination payoff
                group_res.append(round(combination_payoff, 2))
            # Finally Store all the Group Impact Calcluation
            res.append(group_res)

        # res = [ [ -20, -10 for a group1], [ -20, -10 for a group2]]
        # Get the sum of correspoding percentage impact value groupwise
        impact_sum_value_groups = [sum(group_percentages) for group_percentages in zip(*res)]

        # Final list of impact value along with the closest expiry
        impact_value_groups.extend(impact_sum_value_groups)
        impact_columns = ["Date"] + ["{}% Impact".format(int(impact)) for impact in list_of_impact_percent]

        Utils.display_treeview_popup(title, impact_columns, [impact_value_groups])

        # return True















        # res [-20 -10, -5, Total]

        for combination_group, closest_expiry in zip(list_of_combination_groups, list_of_closest_expiry_for_each_group):
            
            multiplier = None
            # Creating a list of the config_leg_object for this group, for getting action, right etc info
            list_of_config_leg_object_for_combination_group = [ _[-1] for _ in combination_group]

            # Calculating the MaxLoss and Max Profit for the Group(acting as a combination)
            combination_payoff = MaxPNLCalculation.get_combination_payoff(
                    list_of_legs_tuple=combination_group,
                    list_of_config_leg_objects=list_of_config_leg_object_for_combination_group,
                    closest_expiry=closest_expiry,
                    multiplier=multiplier,
                )
            
        # Combo Details
        list_of_underlying_contract = []
        list_of_leg_objects = self.list_of_all_leg_objects
        list_of_leg_contract_info_tuple = [(leg_obj.symbol, leg_obj.sec_type, leg_obj.exchange, leg_obj.currency, leg_obj.expiry, leg_obj.right, leg_obj.multiplier, leg_obj.trading_class, leg_obj.underlying_conid) for leg_obj in list_of_leg_objects]

        # Loop through each leg's contract information and create underlying contracts add to the list
        for leg_info, underlying_conid in zip(list_of_leg_contract_info_tuple, list_of_underlying_conids):
            symbol, sec_type, exchange, currency, expiry_date, right, multiplier, trading_class, und_conid = leg_info
            if sec_type == "OPT":
                underlying_sec_type = "STK"
                underlying_multiplier = 1
                underlying_contract = get_contract(
                    symbol=symbol,
                    sec_type=underlying_sec_type,
                    exchange=exchange,
                    currency=currency,
                    multiplier=underlying_multiplier,
                    con_id=und_conid,
                )
                list_of_underlying_contract.append(underlying_contract)
            else:
                underlying_sec_type = "FUT"
                underlying_multiplier = int(multiplier)
                underlying_contract = get_contract(
                    symbol=symbol,
                    sec_type=underlying_sec_type,
                    exchange=exchange,
                    currency=currency,
                    multiplier=underlying_multiplier,
                    con_id=und_conid,
                )
                list_of_underlying_contract.append(underlying_contract)
        
        list_of_leg_strike_action_qty_tuple = [(leg_obj.symbol, leg_obj.strike, leg_obj.con_id, leg_obj.action, leg_obj.qty, leg_obj.expiry, leg_obj.right, leg_obj.multiplier) for leg_obj in list_of_leg_objects]

        list_of_option_contracts = []

        # Loop through each leg's strike, action, quantity, expiry, right, and multiplier and create option contracts, then add to the list
        for _,strike, _,action, quantity, expiry, right_, multiplier_ in list_of_leg_strike_action_qty_tuple:
            option_contract = get_contract(
                symbol,
                sec_type,
                exchange,
                currency,
                expiry,
                strike,
                right_,
                multiplier_,
                trading_class=trading_class,
            )
            list_of_option_contracts.append(option_contract)

        list_of_underlying_and_option_contracts = list_of_underlying_contract + list_of_option_contracts
        generic_tick_list = ""
        snapshot = True
        max_wait_time = 9

        # Fetch Data for all the Contracts
        list_of_bid_ask_price_tuple = asyncio.run(
            MarketDataFetcher.get_current_price_for_list_of_contracts_async(list_of_underlying_and_option_contracts, snapshot)
        )

        list_of_ba_mid = []

        for contract, (bid_price, ask_price,) in zip(list_of_underlying_contract,list_of_bid_ask_price_tuple,):
            if bid_price is None or ask_price is None:
                print(f"bid_price or ask_price is None for contract: {contract}")
                return

            ba_mid = (bid_price + ask_price) / 2
            list_of_ba_mid.append(ba_mid)

        
        print(list_of_ba_mid)
        list_of_expiry_dates = [contract.lastTradeDateOrContractMonth for contract in list_of_option_contracts if contract.lastTradeDateOrContractMonth]
        closest_expiry = min(list_of_expiry_dates)
        # List to store all impact values for each expiry date
        # underlying_price = list_of_ba_mid[0]
        # list_of_leg_premiums = list_of_ba_mid[1:]
        list_of_impact_percent = strategy_variables.list_of_percent_for_impact_calcluation
        impact_values = [
            closest_expiry,
        ]

        # ES, NQ, ES, NQ, NQ
        for underlying_price in list_of_ba_mid:
            for impact_per in list_of_impact_percent:
                underlying_price_per_impact = (underlying_price * (100 + impact_per)) / 100
                combination_payoff = MaxPNLCalculation.get_combination_payoff(
                    list_of_leg_strike_action_qty_tuple,
                    underlying_price_per_impact,
                    closest_expiry,
                )

            impact_values.append(round(combination_payoff, 2))

        # DISPLAY DETAILS of combo
        impact_columns = ["Date"] + ["{}% Impact".format(int(impact)) for impact in list_of_impact_percent]

        Utils.display_treeview_popup(title, impact_columns, [impact_values])

        return True

# It is used to show user the combination details in combination tab of screen GUI
def get_scanner_combination_details_column_and_data_from_combo_object(
    combo_id: int,
):
    try:
        # Scanner Combo Object
        combo_obj = strategy_variables.map_combo_id_to_scanner_combination_object[combo_id]

    except Exception as e:
        # Show error pop up
        error_title = f"Error Scanned Combo ID: {combo_id}"
        error_string = f"Unable to find the Scanned Combination."
        Utils.display_message_popup(error_title, error_string)
        return None

    # Column names, to show inside Combination details screen GUI
    leg_columns_for_combo_detail_gui = strategy_variables.leg_columns_combo_detail_gui

    # List of tuple (for each row in combination details)
    leg_data_tuple_list = []

    # All Legs in combination

    all_legs = combo_obj.list_of_all_leg_objects
    # sec_type = combo_obj.sec_type
    # exchange = combo_obj.exchange
    # currency = combo_obj.currency
    # right = combo_obj.right
    # multiplier = combo_obj.multiplier
    # primary_exchange = combo_obj.primary_exchange
    # trading_class = combo_obj.trading_class

    # Processing legs and getting data for row.
    for leg_obj in all_legs:
        # Init
        action = leg_obj.action
        symbol = leg_obj.symbol
        quantity = leg_obj.qty
        strike_price = leg_obj.strike
        con_id = leg_obj.con_id
        expiry_date = leg_obj.expiry
        sec_type = leg_obj.sec_type
        exchange = leg_obj.exchange
        currency = leg_obj.currency
        right = leg_obj.right
        multiplier = leg_obj.multiplier
        primary_exchange = leg_obj.primary_exchange if leg_obj.primary_exchange else ''
        trading_class = leg_obj.trading_class
        # append values to list
        leg_data_tuple_list.append(
            (
                action,
                symbol,
                sec_type,
                exchange,
                currency,
                quantity,
                expiry_date,
                strike_price,
                right,
                multiplier,
                con_id,
                primary_exchange,
                trading_class,
            )
        )

    return leg_columns_for_combo_detail_gui, leg_data_tuple_list
