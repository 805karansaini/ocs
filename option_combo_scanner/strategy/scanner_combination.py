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
    def dispaly_combination_impact(self):
        combo_id = self.combo_id
        
        try:
            config_obj = strategy_variables.config_object
            
            # List to store underlying_conid for each instrument
            list_of_underlying_conids = []
            
            for config_leg_obj in config_obj.list_of_config_leg_object:
                instrument_id = config_leg_obj.instrument_id
                
                # Retrieve indicator_id and indicator_obj for each instrument
                indicator_id = strategy_variables.map_instrument_to_indicator_id[instrument_id]
                indicator_obj = strategy_variables.map_indicator_id_to_indicator_object[indicator_id]
                underlying_conid = indicator_obj.underlying_conid
                
                list_of_underlying_conids.append(underlying_conid)
        except Exception as e:
            print(f"Error for Combo ID: {combo_id}. Exception: {e}")
            return None
        
        # Combo Details
        list_of_underlying_contract = []
        list_of_leg_objects = self.list_of_all_leg_objects
        list_of_leg_contract_info_tuple = [(leg_obj.symbol, leg_obj.sec_type, leg_obj.exchange, leg_obj.currency, leg_obj.expiry, leg_obj.right, leg_obj.multiplier, leg_obj.trading_class) for leg_obj in list_of_leg_objects]
        
        for leg_info, underlying_conid in zip(list_of_leg_contract_info_tuple, list_of_underlying_conids):
            symbol, sec_type, exchange, currency, expiry_date, right, multiplier, trading_class = leg_info
            if sec_type == "OPT":
                underlying_sec_type = "STK"
                underlying_multiplier = 1
                underlying_contract = get_contract(
                    symbol=symbol,
                    sec_type=underlying_sec_type,
                    exchange=exchange,
                    currency=currency,
                    multiplier=underlying_multiplier,
                    con_id=underlying_conid,
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
                    con_id=underlying_conid,
                )
                list_of_underlying_contract.append(underlying_contract)
        
        list_of_leg_strike_action_qty_tuple = [(leg_obj.strike, leg_obj.action, leg_obj.qty, leg_obj.expiry, leg_obj.right, leg_obj.multiplier) for leg_obj in list_of_leg_objects]

        list_of_option_contracts = []

        for strike, action, quantity, expiry, right_, multiplier_ in list_of_leg_strike_action_qty_tuple:
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

        for contract, (
            bid_price,
            ask_price,
        ) in zip(
            list_of_underlying_and_option_contracts,
            list_of_bid_ask_price_tuple,
        ):
            if bid_price is None or ask_price is None:
                print(f"bid_price or ask_price is None for contract: {contract}")
                return

            ba_mid = (bid_price + ask_price) / 2
            list_of_ba_mid.append(ba_mid)

        # Title for the Scanned Combination Details
        print(list_of_ba_mid)
        list_of_expiry_dates = [contract.lastTradeDateOrContractMonth for contract in list_of_underlying_and_option_contracts if contract.lastTradeDateOrContractMonth]

        # List to store all impact values for each expiry date
        all_impact_values = []

    
        for expiry_date in list_of_expiry_dates:
            for underlying_price in list_of_ba_mid[:2]:
                title = f"Impact of Combo, Combo ID: {combo_id}, Expiry Date: {expiry_date}"
                
                list_of_leg_premiums = list_of_ba_mid[2:]
                list_of_impact_percent = strategy_variables.list_of_percent_for_impact_calcluation
                impact_values = [expiry_date]

                for impact_per in list_of_impact_percent:
                    underlying_price_per_impact = (underlying_price * (100 + impact_per)) / 100
                    combination_payoff = self.get_combination_payoff(
                        list_of_leg_premiums,
                        list_of_leg_strike_action_qty_tuple,
                        underlying_price_per_impact,
                        right,
                        multiplier,
                    )
                    impact_values.append(round(combination_payoff, 2))
                
                # Append the impact values for the current expiry date to all_impact_values
            all_impact_values.append(impact_values)

        # Display the popup with all impact values
            impact_columns = ["Date"] + ["{}% Impact".format(int(impact)) for impact in list_of_impact_percent]
        Utils.display_treeview_popup(title, impact_columns, all_impact_values)

        return True


    def get_combination_payoff(
        self,
        list_of_leg_premiums,
        list_of_leg_strike_action_qty_tuple,
        underlying_price,
        right,
        multiplier,
    ):
        combination_payoff = 0
        for leg_premium, (leg_strike, leg_action, leg_qty, expiry, right_, multiplier_) in zip(list_of_leg_premiums, list_of_leg_strike_action_qty_tuple):
            leg_payoff = self.option_payoff(
                leg_strike,
                right_,
                leg_action,
                1,
                underlying_price,
                int(multiplier_),
                leg_premium,
            )

            combination_payoff += leg_payoff
        return combination_payoff

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
            payoff -= leg_premium * combination_multiplier
        else:
            payoff += leg_premium * combination_multiplier

        return payoff


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
