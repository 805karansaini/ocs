import copy
import datetime
from pprint import pprint

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.strategy_variables import MaxPNLEnum
from option_combo_scanner.strategy.strategy_variables import \
    StrategyVariables as strategy_variables

logger = CustomLogger.logger


class MaxPNLCalculation:

    # Group the combination with same underlying
    @staticmethod
    def create_group_same_und(combination, flag_return_dict=False):
        # Dict for group key as conid and list of values containing the leg_tuples
        grouped_tuples = {}

        for symbol, strike, delta, conid, expiry, bid, ask, iv, underlying_conid, config_leg_obj in combination:
            # Append the leg to group 
            if underlying_conid in grouped_tuples:
                grouped_tuples[underlying_conid].append((symbol, strike, delta, conid, expiry, bid, ask, iv, underlying_conid, config_leg_obj))
            # Create the group key: list and append the leg 
            else:
                grouped_tuples[underlying_conid] = [(symbol, strike, delta, conid, expiry, bid, ask, iv, underlying_conid, config_leg_obj)]

        # If true return the dict
        if flag_return_dict:
            return grouped_tuples
        
        return list(grouped_tuples.values())
    
    # find the closest expiry for the group combination
    @staticmethod
    def find_closest_expiry_for_groups(group_combinations):
        closest_expiry_list = []

        # Loop over each group and update the closest expiry for it
        for group_combination in group_combinations:
            min_expiry = 99999999

            # Update the closest expiry if a closer expiry date is found
            for symbol, strike, delta, _, expiry, _, _, _,_,_ in group_combination:
                if int(expiry) < min_expiry:
                    min_expiry = int(expiry)

            # Append the min_expiry to the list 
            closest_expiry_list.append(str(min_expiry))
        
        return closest_expiry_list

    @staticmethod
    def calcluate_max_pnl(combination, list_of_config_leg_object):
        # Combination
        print(f"Combintaion: {combination}")

        # Mode for Combo Calculation
        flag_overall_nearest_expiry = strategy_variables.calculation_mode_for_combination_max_pnl
        
        # Vairables for total combination max profit and loss
        combo_max_profit = 0
        combo_max_loss = 0

        list_of_leg_tuples = combination
        list_of_leg_tuples_with_config_leg = []
        
        # Adding the config_leg_obj to the leg_tuple
        for leg_tuple, config_leg_obj in zip(list_of_leg_tuples, list_of_config_leg_object):
            temp_ = list(leg_tuple)
            temp_.append(config_leg_obj)
            list_of_leg_tuples_with_config_leg.append(tuple(temp_))
            
        # Grouping the Combination based on underlying
        list_of_combination_groups: list = MaxPNLCalculation.create_group_same_und(list_of_leg_tuples_with_config_leg)
        
        # Get the list of closest expiry for the groups
        list_of_closest_expiry_for_each_group = MaxPNLCalculation.find_closest_expiry_for_groups(list_of_combination_groups)

        # if user select for overall nearest expiry(ONE)
        if flag_overall_nearest_expiry == MaxPNLEnum.ONE:
            # print(f"    Using ONE Mode")
            # get the cloest epxiry for all group 
            cloest_expiry_ = min(list_of_closest_expiry_for_each_group)
            list_of_closest_expiry_for_each_group = [cloest_expiry_] * len(list_of_closest_expiry_for_each_group)
        else:
            # print(f"    Using GNE Mode")
            pass

        # Iterate over the groups, and calculate the Max Profit and Loss for each groups
        for combination_group, closest_expiry in zip(list_of_combination_groups, list_of_closest_expiry_for_each_group):


            # Creating a list of the config_leg_object for this group, for getting action, right etc info
            list_of_config_leg_object_for_combination_group = [ _[-1] for _ in combination_group]
            # print(f"\n    Combination Group: {combination_group}")
            # print(f"      Combination ConfigLegObj: {list_of_config_leg_object_for_combination_group}")

            # Calculating the MaxLoss and Max Profit for the Group(acting as a combination)
            max_loss_combination_group, max_profit_combination_group = MaxPNLCalculation.get_combination_max_loss_and_max_profit(
                    list_of_legs_tuple=combination_group,
                    list_of_config_leg_objects=list_of_config_leg_object_for_combination_group,
                    closest_expiry=closest_expiry,
                )

            # print(f"        Group Max Loss: {max_loss_combination_group}, Group Max Profit: {max_profit_combination_group}\n")
            if max_loss_combination_group and max_profit_combination_group:
                combo_max_profit += (max_profit_combination_group)
                combo_max_loss += (max_loss_combination_group)

        # print(f"    Total Combo Loss: {combo_max_loss}, Total Combo Profit: {combo_max_profit}")

        return combo_max_profit, combo_max_loss
    
    @staticmethod
    def get_combination_max_loss_and_max_profit(list_of_legs_tuple, list_of_config_leg_objects, closest_expiry):
        """
        Called for each combintaion group
        """


        # Setting the default Values
        max_profit = float("-inf")
        max_loss = float("inf")

        # Sort the list_of_legs_tuple based on the STRIKE
        sorted_legs_tuple = sorted(list_of_legs_tuple, key=lambda x: (x[1], x[4]))  

        # Rearrange list_of_config_leg_objects based on the sorting of list_of_legs_tuple
        sorted_indices = [list_of_legs_tuple.index(leg) for leg in sorted_legs_tuple]

        temp_list_of_config_leg_objects = copy.deepcopy(list_of_config_leg_objects)

        # Creating a list of leg_object and Renaming the variable
        list_of_config_leg_objects = [temp_list_of_config_leg_objects[i] for i in sorted_indices]
        list_of_legs_tuple = sorted_legs_tuple

        # print(f"    Combination Leg After Softing: {list_of_legs_tuple}")
        # print(f"    Combination ConfigLegObj After Sorting: {list_of_config_leg_objects}")

        # Calcaulte the combinations premium received
        combination_premium_received = MaxPNLCalculation.calculate_combination_premium(list_of_legs_tuple, list_of_config_leg_objects,)

        # print(f"    Combination Premium: {combination_premium_received}")

        # InstrumentID, and InstrumentObject for multiplier
        instrument_id = list_of_config_leg_objects[0].instrument_id
        if instrument_id not in strategy_variables.map_instrument_id_to_instrument_object:
            print(f"Inside get_combination_max_loss_and_max_profit function could not find instrument id: {instrument_id}")
            return None, None
        instrument_object_for_multiplier = copy.deepcopy(strategy_variables.map_instrument_id_to_instrument_object[instrument_id])

        list_of_combination_payoff_at_all_strikes = []
        # Looping over each Leg Tuples containg STRIKE, and computing the combination payoff if at the expiry the underlying price is equal to leg_tuple.strike
        for i, leg_tuple in enumerate(list_of_legs_tuple):
            
            # Current Leg Strike
            current_leg_strike = leg_tuple[1]
            
            # Get the Left & Left+1 Payoff
            if i == 0:
                left_strike = 0 
                # Get the payoff for left strike: 0
                strike_zero_payoff = MaxPNLCalculation.get_combination_payoff(
                    list_of_legs_tuple,
                    list_of_config_leg_objects,
                    underlying_strike_price=left_strike,
                    closest_expiry=closest_expiry,
                )

                # Add the Combination payoff at Strike 0
                list_of_combination_payoff_at_all_strikes.append(round(strike_zero_payoff, 2))

                # Get the payoff for left_strike + 1
                strike_one_payoff = MaxPNLCalculation.get_combination_payoff(
                    list_of_legs_tuple,
                    list_of_config_leg_objects,
                    underlying_strike_price=left_strike + 1,
                    closest_expiry=closest_expiry,
                )

    
                # getting the payoff(left) - payoff(left + 1)
                slope_left_numerator = (strike_zero_payoff - strike_one_payoff)/int(instrument_object_for_multiplier.multiplier)
                slope_left_deno = 1

            # Get the combination payoff for the strike of current leg
            combo_pay_off_for_current_strike = MaxPNLCalculation.get_combination_payoff(
                list_of_legs_tuple,
                list_of_config_leg_objects,
                current_leg_strike,
                closest_expiry,
            )
            list_of_combination_payoff_at_all_strikes.append(round(combo_pay_off_for_current_strike, 2))
            # print(f"UndPrice At Expiry {leg_tuple[1]}, Combination Payoff: {combo_pay_off_for_current_strike}")

            # Get the Right & Right-1 Payoff
            if i == len(list_of_legs_tuple) - 1:

                # Right Strike is 2*MaxStrike
                right_strike = current_leg_strike * 2

                # Strike N * 2: Get the next Strike payoff for Strike N * 2
                max_strike_right_payoff = MaxPNLCalculation.get_combination_payoff(
                    list_of_legs_tuple,
                    list_of_config_leg_objects,
                    underlying_strike_price=right_strike,
                    closest_expiry=closest_expiry,
                )

                # Add the Combination payoff at Strike Strike Right
                list_of_combination_payoff_at_all_strikes.append(round(max_strike_right_payoff, 2))

                # Get payoff for right - 1
                max_strike_right_one_payoff = MaxPNLCalculation.get_combination_payoff(
                    list_of_legs_tuple,
                    list_of_config_leg_objects,
                    underlying_strike_price=right_strike - 1,
                    closest_expiry=closest_expiry,
                )
                
                # TODO - comment 
                # getting the payoff(right) - payoff(right - 1) and divide by the multiplier
                slope_right_numerator = (max_strike_right_payoff - max_strike_right_one_payoff)/int(instrument_object_for_multiplier.multiplier)
                slope_right_deno = 1

                # print(f"LegTuple: {leg_tuple} {combo_pay_off_for_current_strike= } {slope_right_numerator= } {strike_right= }")

        # TODO- print list_of_combination_payoff_at_all_strikes
        print(f"        List of Combination Payoff W/P Prem. for all Strikes: {list_of_combination_payoff_at_all_strikes}")
        print(f"        Premimum: {combination_premium_received}")
        
        # TODO - list_of_combination_payoff_at_all_strikes + combination premium
        list_of_combination_payoff_at_all_strikes = [ _ + combination_premium_received for _ in list_of_combination_payoff_at_all_strikes]
        print(f"        List of Combination Payoff W/ Prem for all Strikes: {list_of_combination_payoff_at_all_strikes}")

        

        print(f"        Payoff(right) - Payoff(right-1) {slope_right_numerator}")
        print(f"        Payoff(left) - Payoff(left+1) {slope_left_numerator}")

        # Update the Max Profit
        if abs(slope_right_numerator/slope_right_deno) > 0.90:
            if slope_right_numerator > 0:
                max_profit = float("inf")
                list_of_combination_payoff_at_all_strikes.pop()
            elif slope_right_numerator < 0:
                max_loss = float("-inf")
                list_of_combination_payoff_at_all_strikes.pop()
                    
        if abs(slope_left_numerator/slope_left_deno) > 0.90:
            if slope_left_numerator > 0:
                max_profit = float("inf")
                list_of_combination_payoff_at_all_strikes.pop(0)
            elif slope_left_numerator < 0:
                max_loss = float("-inf")
                list_of_combination_payoff_at_all_strikes.pop(0)
                
        # Updating the max profit and loss
        if max_profit != float("inf"):
            max_profit = max(list_of_combination_payoff_at_all_strikes)

        if max_loss != float("-inf"):
            max_loss = min(list_of_combination_payoff_at_all_strikes)

        return max_loss, max_profit


    # Calulating Combination Payoff for Strike
    @staticmethod
    def get_combination_payoff(list_of_legs_tuple, list_of_config_leg_object, underlying_strike_price, closest_expiry, multiplier=None):
        print(f"\n      Get Combintaion Payoff:- LegTuple: {list_of_legs_tuple} underlying_strike_price,closest_expiry {[underlying_strike_price, closest_expiry,]}")
        
        # Default Values        
        combination_payoff = 0
        
        # For each leg in the combinations, caclculate the option-payoff if the underlying expiries at 'underlying_strike_price'
        for leg, config_leg_obj in zip(list_of_legs_tuple, list_of_config_leg_object):
            
            # InstrumentID, and InstrumentObject for multiplier
            instrument_id = config_leg_obj.instrument_id
            quantity = config_leg_obj.quantity

            # Get the combinaition Mmultiplier if instrument exists
            if instrument_id not in strategy_variables.map_instrument_id_to_instrument_object:
                print(f"Inside get_combination_payoff function could not find instrument id: {instrument_id}")
                return 0
            else:
                if multiplier == None:
                    multiplier = int(strategy_variables.map_instrument_id_to_instrument_object[instrument_id].multiplier)
                else:
                    multiplier = multiplier
                    
            # Unpacking the combination leg tuple
            symbol, option_strike,_, _, leg_expiry, bid, ask, leg_iv,_, _ = leg
            intial_leg_premium = 0
            
            # Getting the intial_leg_premium
            try:
                if bid == float("nan") or ask == float("nan"):
                    intial_leg_premium = 0
                else:
                    intial_leg_premium = (bid + ask) / 2
            except Exception as e:
                intial_leg_premium = 0

            
            # Calcluate OptionPayoff for the expiry same as closest expiry, holds the TimeValueOfOption=0
            if leg_expiry == closest_expiry:
                # print(f"        Calcluate OptionPayoff for the expiry same as closest expiry, holds the TimeValueOfOption=0")

                leg_payoff, _ = MaxPNLCalculation.option_payoff(
                    option_strike,
                    config_leg_obj.right,
                    config_leg_obj.action,
                    1,
                    float(underlying_strike_price),
                    int(multiplier),
                    intial_leg_premium,
                )
    
                # Add to combination off the sign is already adjusted in the option_payoff method
                combination_payoff += (leg_payoff * quantity)
                # print(f"        Leg Payoff: {leg_payoff}, Combination Payoff: {combination_payoff}")

            # Calculate the OptionPayoff for the further expiry than the closest expiry, holds the TimeValueOfOption
            else:
                # print(f"        Calculate the OptionPayoff for the further expiry than the closest expiry, holds the TimeValueOfOption")
                
                # Getting the TTE from the closest expiry in Years
                leg_expiry_obj = datetime.datetime.strptime(leg_expiry, "%Y%m%d")
                closest_expiry_obj = datetime.datetime.strptime(closest_expiry, "%Y%m%d")
                time_to_expiration = abs(leg_expiry_obj - closest_expiry_obj).days

                # Handle Case where 'time_to_expiration' is 0
                if time_to_expiration == 0:
                    time_to_expiration = 1

                time_to_expiration = (time_to_expiration) / 365

                # Theoretical Premium
                leg_payoff = Utils.get_theoretical_premium(underlying_strike_price, strategy_variables.riskfree_rate1, 0, time_to_expiration, option_strike, leg_iv, config_leg_obj.right)                
                
                # Add to combination PayOff
                leg_payoff = 1*leg_payoff if config_leg_obj.action.upper() == "BUY" else -1*leg_payoff
                leg_payoff *= int(multiplier)
                
                combination_payoff += (leg_payoff * quantity)
                # print(f"        Leg Payoff(Th.Prem): {leg_payoff}, Combination Payoff: {combination_payoff}")
                # print(f"        Theortical Premimum Function Inputs: {underlying_strike_price= }, RR1: {strategy_variables.riskfree_rate1}, TTE: {time_to_expiration}, Strike:{option_strike}, IV: {leg_iv}, Right: {config_leg_obj.right}")
                # print(f"        Theortical Premimum: Payoff/Ther.Prem: {leg_payoff} for Strike: {option_strike} for Expiry: {leg_expiry}")

            # print(f"Leg PayOff: {leg_payoff} Strike: {option_strike} Premium: {leg_premium}")
        return combination_payoff


    # Function to calculate the leg wise option payoff
    @staticmethod
    def option_payoff(
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
        # print(f"        Option Payoff: Option Strike: {option_strike}, Underlying_price_expiry: {underlying_price_expiry}, Leg_premium: {leg_premium}, Quantity: {quantity}, OptionType: {option_type}, Action: {buy_or_sell}, Multiplier: {combination_multiplier}")
        leg_premium_received = 0
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

    
    @staticmethod
    def calculate_leg_premium(
        buy_or_sell,
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
    
        # Consider the Option Premium as well
        if buy_or_sell == "BUY":
            leg_premium_received -= leg_premium * combination_multiplier
        else:
            leg_premium_received += leg_premium * combination_multiplier

        return leg_premium_received

    
    @staticmethod
    def calculate_combination_premium(list_of_legs_tuple, list_of_config_leg_object,):

        # Default Values        
        combination_premium_received = 0
        
        # For each leg in the combinations, caclculate the option-payoff if the underlying expiries at 'underlying_strike_price'
        for leg, config_leg_obj in zip(list_of_legs_tuple, list_of_config_leg_object):
            
            # InstrumentID, and InstrumentObject for multiplier
            instrument_id = config_leg_obj.instrument_id
            quantity = config_leg_obj.quantity
            if instrument_id not in strategy_variables.map_instrument_id_to_instrument_object:
                continue
            instrument_object_for_leg_prem = copy.deepcopy(strategy_variables.map_instrument_id_to_instrument_object[instrument_id])

            # Unpacking the combination leg tuple
            symbol, option_strike,_, _, leg_expiry, bid, ask, leg_iv,_, _ = leg
            intial_leg_premium = 0
            
            # Getting the intial_leg_premium
            try:
                if bid == float("nan") or ask == float("nan"):
                    intial_leg_premium = 0
                else:
                    intial_leg_premium = (bid + ask) / 2
            except Exception as e:
                intial_leg_premium = 0

            leg_premium_received = MaxPNLCalculation.calculate_leg_premium(
                config_leg_obj.action,
                int(instrument_object_for_leg_prem.multiplier),
                intial_leg_premium,
            )

            combination_premium_received += (leg_premium_received * quantity)

        return combination_premium_received


    