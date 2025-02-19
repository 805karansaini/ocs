import asyncio
import copy
import warnings
from pprint import pprint

import pandas as pd

from com.contracts import get_contract, get_contract_details
from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.indicators_calculator.market_data_fetcher import (
    MarketDataFetcher,
)
from option_combo_scanner.strategy.max_loss_profit_calculation import MaxPNLCalculation
from option_combo_scanner.strategy.strategy_variables import (
    StrategyVariables as strategy_variables,
)

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
            self.max_loss = (
                float("-inf") if "inf" in self.max_loss else int(float(self.max_loss))
            )
        except Exception as e:
            pass
            # print(f"Error for COmbo ID: ", self.combo_id, "max_loss", self.max_loss)

        try:
            self.max_profit = (
                float("inf")
                if "inf" in self.max_profit
                else int(float(self.max_profit))
            )
        except Exception as e:
            pass

            # print(f"Error for COmbo ID: ", self.combo_id, "max_profit", self.max_profit)

        # Set the combination description
        self.description = self.get_combo_description()

        # Map combination_id to combination object
        self.map_combo_id_to_scanner_combination_object()

    def map_combo_id_to_scanner_combination_object(self):
        strategy_variables.map_combo_id_to_scanner_combination_object[self.combo_id] = (
            self
        )

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
        warnings.filterwarnings("ignore", category=FutureWarning)

        strategy_variables.scanner_combo_table_df = pd.concat(
            [strategy_variables.scanner_combo_table_df, row],
            ignore_index=True,
        )

    def remove_scanned_combo_from_system(self):
        # Remove row from dataframe
        strategy_variables.scanner_combo_table_df = (
            strategy_variables.scanner_combo_table_df.drop(
                strategy_variables.scanner_combo_table_df[
                    strategy_variables.scanner_combo_table_df["Combo ID"]
                    == self.combo_id
                ].index
            )
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

    def dispaly_combination_impact(
        self,
    ):
        # Getitng the CombinationObj, ComboID, List of ComboLegObj
        combo_obj = self
        combo_id = combo_obj.combo_id
        list_of_combo_leg_object = combo_obj.list_of_all_leg_objects

        # Config ID, Confg Object, ListOfConfigLegObj
        config_id = combo_obj.config_id

        if not config_id in strategy_variables.map_config_id_to_config_object:
            Utils.display_message_popup(
                "Error",
                f"Can not compute the Impact: Unable to find Config ID: {config_id}",
            )
            return

        config_obj = copy.deepcopy(
            strategy_variables.map_config_id_to_config_object[config_id]
        )
        list_of_config_leg_object = config_obj.list_of_config_leg_object

        # Creating the list_of_combo_leg_tuples_with_config_leg
        list_of_combo_leg_tuples_with_config_leg = []

        # Adding the config_leg_obj to the leg_tuple
        for combo_leg_object, config_leg_obj in zip(
            list_of_combo_leg_object, list_of_config_leg_object
        ):
            temp_list = [
                combo_leg_object.symbol,
                combo_leg_object.strike,
                None,
                None,
                combo_leg_object.expiry,
                None,
                None,
                None,
                combo_leg_object.underlying_conid,
                config_leg_obj,
            ]
            list_of_combo_leg_tuples_with_config_leg.append(tuple(temp_list))

        # Creating the Groups Based on the Underlying
        map_underlying_conid_to_list_of_combination_group: dict = (
            MaxPNLCalculation.create_group_same_und(
                list_of_combo_leg_tuples_with_config_leg, flag_return_dict=True
            )
        )
        list_of_combination_groups = list(
            map_underlying_conid_to_list_of_combination_group.values()
        )

        # Get the list of closest expiry for the groups
        list_of_closest_expiry_for_each_group = (
            MaxPNLCalculation.find_closest_expiry_for_groups(
                list_of_combination_groups,
            )
        )

        # Alway use ONE Overall Nearest Expiry Calculation Mode
        closest_expiry = min(list_of_closest_expiry_for_each_group)

        # 1.a We want to get the Current Price of Underlying Contract.
        # 1.b We want to get the Current Market Data for Option Contracts.
        # 1.c if required data is not available, throw an error popup.
        # 2. Manupulate the leg tuples, meaning update the None to fetched values
        # 3. Impact

        # List of underlying contracts
        list_of_underlying_contract = []

        # List of option contracts
        list_of_option_contracts = []

        list_of_multiplier_for_combo_group = []

        # Underlying Contracts
        for (
            underlying_conid,
            combination_group,
        ) in map_underlying_conid_to_list_of_combination_group.items():
            # Unpacking the first leg
            symbol, _, _, _, _, _, _, _, underlying_conid, config_leg_obj = (
                combination_group[0]
            )

            # Get the Instrument SecType
            _instrument_id = int(config_leg_obj.instrument_id)

            # Show error popup that instrument id is not present
            if (
                _instrument_id
                not in strategy_variables.map_instrument_id_to_instrument_object
            ):
                Utils.display_message_popup(
                    "Error",
                    f"Can not compute the Impact: Unable to find Instrument ID: {_instrument_id}",
                )
                return

            # Get the instrument object details for contract creation
            instrument_obj_ = copy.deepcopy(
                strategy_variables.map_instrument_id_to_instrument_object[
                    _instrument_id
                ]
            )
            instrument_sec_type = instrument_obj_.sec_type
            instrument_exchange = instrument_obj_.exchange
            instrument_currency = instrument_obj_.currency
            instrument_multiplier = instrument_obj_.multiplier
            instrument_trading_class = instrument_obj_.trading_class

            # Appending the group/instrument multiplier
            list_of_multiplier_for_combo_group.append(instrument_multiplier)

            # If the Intrument SecType is OPT, create underlying STK contract
            if instrument_sec_type in ["OPT", "IND"]:
                if instrument_sec_type == "OPT":
                    underlying_sec_type = "STK"
                else:
                    underlying_sec_type = "IND"
                underlying_multiplier = 1

                underlying_contract = get_contract(
                    symbol=symbol,
                    sec_type=underlying_sec_type,
                    exchange=instrument_exchange,
                    currency=instrument_currency,
                    multiplier=underlying_multiplier,
                    con_id=underlying_conid,
                )

            else:
                # Create underlying FUT contract
                underlying_sec_type = "FUT"
                underlying_multiplier = int(instrument_multiplier)
                underlying_contract = get_contract(
                    symbol=symbol,
                    sec_type=underlying_sec_type,
                    exchange=instrument_exchange,
                    currency=instrument_currency,
                    multiplier=underlying_multiplier,
                    con_id=underlying_conid,
                )
                # Complete contract with expiry and everything
                contract_details = get_contract_details(underlying_contract)
                underlying_contract.lastTradeDateOrContractMonth = (
                    contract_details.contract.lastTradeDateOrContractMonth
                )
                #  '{"contract_type":"FUT","ticker":"ES","right":"","expiry":"20240621","strike":0.0,"currency":"USD","trading_class":"ES","exchange":"CME","multiplier":50}', 'duration': 27, 'bar_size': 1, 'bar_unit': 'hour', 'bar_type': 'BID', 'flag_rth_only': True}}

            # Append the underlying contract to the list
            list_of_underlying_contract.append(underlying_contract)

            # Creating & Appending the OPT contracts for the group in the list
            for combo_leg_tuple in combination_group:
                (
                    symbol,
                    strike,
                    delta,
                    conid,
                    expiry,
                    bid,
                    ask,
                    iv,
                    underlying_conid,
                    config_leg_obj,
                ) = combo_leg_tuple

                if instrument_sec_type in ["OPT", "FOP"]:
                    _opt_instrument_sec_type = instrument_sec_type
                    _opt_instrument_exchange = instrument_exchange
                elif instrument_sec_type in ["IND"]:
                    _opt_instrument_sec_type = "OPT"
                    _opt_instrument_exchange = "SMART"

                # Right from the ConfigLegObject
                right = config_leg_obj.right

                option_contract = get_contract(
                    symbol,
                    _opt_instrument_sec_type,
                    _opt_instrument_exchange,
                    instrument_currency,
                    expiry,
                    strike,
                    right,
                    instrument_multiplier,
                    trading_class=instrument_trading_class,
                )
                list_of_option_contracts.append(option_contract)

        # Merged in list of both underlying and option contract
        list_underlying_and_option_contracts = (
            list_of_underlying_contract + list_of_option_contracts
        )

        generic_tick_list = "101"
        snapshot = False
        flag_market_open = variables.flag_market_open
        max_wait_time = 9

        # Fetch Data for all the Contracts
        list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple = asyncio.run(
            MarketDataFetcher.get_option_delta_and_implied_volatility_for_contracts_list_async(
                list_underlying_and_option_contracts,
                flag_market_open,
                generic_tick_list=generic_tick_list,
                snapshot=snapshot,
                max_wait_time=max_wait_time,
            )
        )

        # Splitting the list for underlying and opt contracts
        number_of_groups = len(list_of_combination_groups)
        underlying_list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple = list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple[
            :number_of_groups
        ]
        options_list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple = list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple[
            number_of_groups:
        ]

        list_of_underlying_price_for_combo_group = []

        # Perform Validation, to make sure we have all the data to compute impact.
        # i.e. underlying: bid, ask | option: bid,ask,iv
        for (
            delta,
            iv_ask,
            iv_bid,
            iv_last,
            bid_price,
            ask_price,
            call_oi,
            put_oi,
            _,
            _,
            _,
            _,
            last_price,
        ), __und_contract in zip(
            underlying_list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple,
            list_of_underlying_contract,
        ):
            if __und_contract.secType == "IND" and last_price is not None:
                list_of_underlying_price_for_combo_group.append(last_price)
            elif __und_contract.secType != "IND" and (
                bid_price is not None or ask_price is not None
            ):
                ba_mid = (bid_price + ask_price) / 2
                list_of_underlying_price_for_combo_group.append(ba_mid)
            else:
                Utils.display_message_popup(
                    f"Error Combo ID: {combo_id}",
                    f"Bid Price or Ask Price is None",
                )
                return

        temp_list_of_combination_legs = []
        list_of_number_of_legs_in_combo = []

        for combination_group in list_of_combination_groups:
            N = len(combination_group)
            list_of_number_of_legs_in_combo.append(N)

            for leg_tuple in combination_group:
                temp_list_of_combination_legs.append(list(leg_tuple))

        # Update the legs_tuple for each combination group.
        for i, (
            leg_info_list,
            (
                delta,
                iv_ask,
                iv_bid,
                iv_last,
                bid_price,
                ask_price,
                call_oi,
                put_oi,
                _,
                _,
                _,
                _,
                last_price,
            ),
        ) in enumerate(
            zip(
                temp_list_of_combination_legs,
                options_list_of_delta_iv_ask_iv_bid_iv_last_bid_ask_price_call_oi_put_oi_tuple,
            )
        ):
            if bid_price is None or ask_price is None or iv_ask is None:
                # Show error popup and return
                Utils.display_message_popup(
                    f"Error Combo ID: {combo_id}",
                    f"Bid Price or Ask Price or IV is None",
                )
                return

                # return False
            else:
                temp_list_of_combination_legs[i][5] = bid_price
                temp_list_of_combination_legs[i][6] = ask_price
                temp_list_of_combination_legs[i][7] = iv_ask

        new_list_of_combination_groups = []

        start = 0

        for legs__ in list_of_number_of_legs_in_combo:
            # Start index for this new group
            end = start + legs__

            # New Group
            new_group = temp_list_of_combination_legs[start:end]
            new_list_of_combination_groups.append(new_group)

            # Update the start index
            start = end

        # Rename the variable
        list_of_combo_group = new_list_of_combination_groups

        res = []

        # Title and List of Impacts in the UserInputs
        title = f"Impact of Combo, Combo ID : {combo_id}"
        list_of_impact_percent = (
            strategy_variables.list_of_percent_for_impact_calcluation
        )

        # Closest Expiry for displaying
        impact_value_groups = [closest_expiry]

        # For each group(same underlying) calcluate the impact
        for underlying_price, combination_group, multiplier in zip(
            list_of_underlying_price_for_combo_group,
            list_of_combo_group,
            list_of_multiplier_for_combo_group,
        ):
            # print(f"Underlying Price: {underlying_price}")
            # print(f"Combination Group: {combination_group}\n")

            list_of_config_leg_objects = [_[-1] for _ in combination_group]

            # Calcaulte the combinations premium received
            combination_premium_received = (
                MaxPNLCalculation.calculate_combination_premium(
                    combination_group,
                    list_of_config_leg_objects,
                )
            )

            # Sort the combination_group based on the STRIKE, expiry
            sorted_legs_tuple = sorted(combination_group, key=lambda x: (x[1], x[4]))

            # Rearrange list_of_config_leg_objects based on the sorting of combination_group
            sorted_indices = [combination_group.index(leg) for leg in sorted_legs_tuple]

            temp_list_of_config_leg_objects = copy.deepcopy(list_of_config_leg_objects)

            # Creating a list of leg_object and Renaming the variable
            list_of_config_leg_objects = [
                temp_list_of_config_leg_objects[i] for i in sorted_indices
            ]
            combination_group = sorted_legs_tuple

            group_res = []
            # Loop over the list of impact percent
            for impact_per in list_of_impact_percent:
                underlying_strike_price = (underlying_price * (100 + impact_per)) / 100

                # Get the combination payoff
                combination_payoff = MaxPNLCalculation.get_combination_payoff(
                    list_of_legs_tuple=combination_group,
                    list_of_config_leg_object=list_of_config_leg_objects,
                    underlying_strike_price=underlying_strike_price,
                    closest_expiry=closest_expiry,
                    multiplier=multiplier,
                )

                combination_payoff += combination_premium_received

                # Store the groupwise combination payoff
                group_res.append(round(combination_payoff, 2))
            # Finally Store all the Group Impact Calcluation
            res.append(group_res)

        # res = [ [ -20, -10 for a group1], [ -20, -10 for a group2]]
        # Get the sum of correspoding percentage impact value groupwise
        impact_sum_value_groups = [
            round(sum(group_percentages), 2) for group_percentages in zip(*res)
        ]

        # Final list of impact value along with the closest expiry
        impact_value_groups.extend(impact_sum_value_groups)
        impact_columns = ["Date"] + [
            "{}% Impact".format(int(impact)) for impact in list_of_impact_percent
        ]

        Utils.display_treeview_popup(title, impact_columns, [impact_value_groups])

        return True


# It is used to show user the combination details in combination tab of screen GUI
def get_scanner_combination_details_column_and_data_from_combo_object(
    combo_id: int,
):
    try:
        # Scanner Combo Object
        combo_obj = strategy_variables.map_combo_id_to_scanner_combination_object[
            combo_id
        ]

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
        primary_exchange = leg_obj.primary_exchange if leg_obj.primary_exchange else ""
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
