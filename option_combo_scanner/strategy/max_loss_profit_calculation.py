import copy
import datetime
from pprint import pprint

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.strategy.strategy_variables import (
    StrategyVariables as strategy_variables,
)

logger = CustomLogger.logger


class MaxPNLCalculation:

    # Group the combination with same underlying
    @staticmethod
    def create_group_same_und(combination):
        grouped_tuples = {}

        for symbol, strike, delta, conid, expiry, bid, ask, iv, underlying_conid, config_leg_obj in combination:
            if underlying_conid in grouped_tuples:
                grouped_tuples[underlying_conid].append((symbol, strike, delta, conid, expiry, bid, ask, iv, underlying_conid, config_leg_obj))
            else:
                grouped_tuples[underlying_conid] = [(symbol, strike, delta, conid, expiry, bid, ask, iv, underlying_conid, config_leg_obj)]

        return list(grouped_tuples.values())
    
    # find the closest expiry for the group combination
    @staticmethod
    def find_closest_expiry(group_combinations):
        closest_expiry_list = []
        for group_combination in group_combinations:
            min_expiry = 99999999
            for symbol, strike, delta, _, expiry, _, _, _,_,_ in group_combination:
                if int(expiry) < min_expiry:
                    min_expiry = int(expiry)
            closest_expiry_list.append(str(min_expiry))
        return closest_expiry_list

    @staticmethod
    def calcluate_maxpnl(combination, list_of_config_leg_object):
        total_grp_max_profit = total_grp_max_loss = 0
        # Combination
        print(f"Combintaion: {combination}")

        list_of_leg_tuples = combination
        combination = []
        for leg_tuple, config_leg_obj in zip(list_of_leg_tuples, list_of_config_leg_object):
            temp_ = list(leg_tuple)
            temp_.append(config_leg_obj)
            combination.append(tuple(temp_))
            
        # Group Combination based on same uderlying
        group_combinations: list = MaxPNLCalculation.create_group_same_und(combination)
        
        # print(group_combinations)
        # get the list of closest expiry for the groups
        list_of_closest_expiry = MaxPNLCalculation.find_closest_expiry(group_combinations)

        # iterate over the group to get payoff for group combination
        for group_combination, closest_expiry in zip(group_combinations, list_of_closest_expiry):
            #   Groups TODO
            print(f"    Group Combination: {group_combination}")
            sub_list_of_config_leg_object = [ _[-1] for _ in group_combination]

            # print(group_combination, closest_expiry, config_leg)
            max_loss, max_profit = MaxPNLCalculation.get_combination_max_loss_and_max_profit(
                    list_of_legs_tuple=group_combination,
                    list_of_config_leg_objects=sub_list_of_config_leg_object,
                    closest_expiry = closest_expiry,
                )
            

            print(f"        Max Loss: {max_loss}, Max Profit: {max_profit}\n")
            
            total_grp_max_profit += (max_profit)
            total_grp_max_loss += (max_loss)

        print(f"    Total Combo Profit: {total_grp_max_profit}, Total Combo Loss: {total_grp_max_loss}")
        return total_grp_max_profit, total_grp_max_loss
    
    @staticmethod
    def get_combination_max_loss_and_max_profit(list_of_legs_tuple, list_of_config_leg_objects, closest_expiry):
        max_profit = float("-inf")
        max_loss = float("inf")

        # Sort list_of_legs_tuple
        sorted_legs_tuple = sorted(
            list_of_legs_tuple, key=lambda x: x[1]
        )  # Assuming tuple elements to be sorted based on the first element

        # Rearrange list_of_config_leg_objects based on the sorting of list_of_legs_tuple
        sorted_indices = [list_of_legs_tuple.index(leg) for leg in sorted_legs_tuple]
        # print(list_of_config_leg_objects)
        sorted_config_leg_objects = [list_of_config_leg_objects[i] for i in sorted_indices]

        # print(sorted_config_leg_objects)
        list_of_legs_tuple = sorted_legs_tuple
        list_of_config_leg_objects = sorted_config_leg_objects
        for i, leg_tuple in enumerate(list_of_legs_tuple):
        
            # Get the combination payoff for the strike of current leg
            combo_pay_off_for_current_strike, combination_premium_received = MaxPNLCalculation.get_combination_payoff(
                list_of_legs_tuple,
                list_of_config_leg_objects,
                leg_tuple[1],
                closest_expiry,
            )
            combo_pay_off_for_current_strike = round(combo_pay_off_for_current_strike)

            # print(f"UndPrice At Expiry {leg_tuple[1]}, Combination Payoff: {combo_pay_off_for_current_strike}")
            # Max Profit is max of (Payoff Strike1, PayoffStrike2...)
            max_profit = max(max_profit, combo_pay_off_for_current_strike)
            max_loss = min(max_loss, combo_pay_off_for_current_strike)

            if i == 0:
                # Get the payoff for left strike: 0
                strike_zero_payoff, l_combination_premium_received = MaxPNLCalculation.get_combination_payoff(
                    list_of_legs_tuple,
                    list_of_config_leg_objects,
                    0,
                    closest_expiry,
                )
                # Get the payoff for left + 1
                strike_one_payoff, l_1_combination_premium_received = MaxPNLCalculation.get_combination_payoff(
                    list_of_legs_tuple,
                    list_of_config_leg_objects,
                    1,
                    closest_expiry,
                )

                # [payoff(left) - payoff(left+1)]
                slope_left_numerator = strike_zero_payoff - strike_one_payoff
                strike_left = 0
                strike_left_plus_one = 1
                # [strike(left+1) - strike[(left)]
                slope_left_deno = strike_left_plus_one - strike_left


            # Get the Right Payoff for Max Strike N
            if i == len(list_of_legs_tuple) - 1:
                # Strike N * 2: Get the next Strike payoff for Strike N * 2
                max_strike_right_payoff, r_combination_premium_received = MaxPNLCalculation.get_combination_payoff(
                    list_of_legs_tuple,
                    list_of_config_leg_objects,
                    list_of_legs_tuple[i][1] * 2,
                    closest_expiry,
                )
                # Get payoff for right - 1
                max_strike_right_one_payoff, r_1_combination_premium_received = MaxPNLCalculation.get_combination_payoff(
                    list_of_legs_tuple,
                    list_of_config_leg_objects,
                    (list_of_legs_tuple[i][1] * 2) - 1,
                    closest_expiry,
                )
                # [payoff(right) - payoff(right-1)] 
                slope_right_numerator = max_strike_right_payoff - max_strike_right_one_payoff
                strike_right = list_of_legs_tuple[i][1] * 2
                strike_right_minus_one = (list_of_legs_tuple[i][1] * 2) - 1
                # [strike(right) - strike[(right -1)]
                slope_right_deno = strike_right - strike_right_minus_one

                # print(f"LegTuple: {leg_tuple} {combo_pay_off_for_current_strike= } {slope_right_numerator= } {strike_right= }")
        
        # Print WIthout Premimum
        print(f"        Without Premimum, Profit : {max_profit}, Loss: {max_loss}")
        print(f"        Premimum: {combination_premium_received}")
        # Premium
        # Premium Added
        # Final Premium
        max_profit += round(combination_premium_received, 2)
        max_loss += round(combination_premium_received, 2)
        print(f"        With Premimum, Profit : {max_profit}, Loss: {max_loss}")
        print(f"        Payoff(right) - Payoff(right-1) {slope_right_numerator}")
        print(f"        Strike(right) - Strike[(right -1) {slope_right_deno}")
        print(f"        Payoff(left) - Payoff(left+1) {slope_left_numerator}")
        print(f"        Strike(left+1) - Strike[(left) {slope_left_deno}")


        # if [payoff(right) - payoff(right-1)] / [strike(right) - strike[(right -1)] > 0.95 -> profit is infinite
        # if [payoff(left) - payoff(left+1)] / [strike(left+1) - strike[(left)] > 0.95 -> profit is infinite
        # if [payoff(right) - payoff(right-1)] / [strike(right) - strike[(right -1)] < -0.95 -> loss is infinite
        # if [payoff(left) - payoff(left+1)] / [strike(left+1) - strike[(left)] < -0.95 -> loss is infinite

        if slope_right_numerator/slope_right_deno > 0.95:
            max_profit = float("inf")

        if slope_left_numerator/slope_left_deno > 0.95:
            max_profit = float("inf")

        if slope_right_numerator/slope_right_deno < -0.95:
            max_loss = float("-inf")

        if slope_left_numerator/slope_left_deno < -0.95:
            max_loss = float("-inf")


        return max_loss, max_profit



    # Calulating Combination Payoff for Strike
    @staticmethod
    def get_combination_payoff(list_of_legs_tuple, list_of_config_leg_object, underlying_strike_price, closest_expiry):
        combination_premium_received = 0
        combination_payoff = 0
        for leg, config_leg_obj in zip(list_of_legs_tuple, list_of_config_leg_object):
            instrument_id = config_leg_obj.instrument_id
            instrument_object_for_leg_prem = copy.deepcopy(strategy_variables.map_instrument_id_to_instrument_object[instrument_id])
            symbol, option_strike,_, _, leg_expiry, bid, ask, leg_iv,_, _ = leg
            leg_premium = 0
            try:
                if bid == float("nan") or ask == float("nan"):
                    leg_premium = 0
                else:
                    leg_premium = (bid + ask) / 2

            except Exception as e:
                # TODO REMOVE IT
                print(f"Could not get the bid and ask for Strike: {option_strike}")

            # Calcluate Payoff for trivial case of same as closest expiry
            if leg_expiry == closest_expiry:
                leg_payoff, leg_premium_received = MaxPNLCalculation.option_payoff(
                    option_strike,
                    config_leg_obj.right,
                    config_leg_obj.action,
                    1,
                    float(underlying_strike_price),
                    int(instrument_object_for_leg_prem.multiplier),
                    leg_premium,
                )
            else:
                # get_theoretical_premium(S, r1, r2, t, X, sigma, opt_type):
                leg_expiry_obj = datetime.datetime.strptime(leg_expiry, "%Y%m%d")
                closest_expiry_obj = datetime.datetime.strptime(closest_expiry, "%Y%m%d")
                time_to_expiration = abs(leg_expiry_obj - closest_expiry_obj).days
                # get time to time_to_expiration
                time_to_expiration = (time_to_expiration) / 365

                # get theoretical_premimum
                print(f"        Theortical Premimum Function Inputs: {underlying_strike_price= }, {strategy_variables.riskfree_rate1= }, {time_to_expiration= }, {option_strike= }, {leg_iv= }, {config_leg_obj.right= }")
                intrintic_plus_time_value = Utils.get_theoretical_premium(underlying_strike_price, strategy_variables.riskfree_rate1, 0, time_to_expiration, option_strike, leg_iv, config_leg_obj.right)                
                print(f"        Theortical Premimum: {intrintic_plus_time_value= } for {option_strike= } for {leg_expiry= }")
                # calculate leg payoff for case where leg expiry is later than closest expiry
                """
                option_strike: Strike of the Leg
                option_type: CALL/PUT
                buy_or_sell: BUY/SELL
                quantity: Qty of Leg
                underlying_price_expiry: Price of option at expiry
                """

                # leg_payoff, leg_premium_received = MaxPNLCalculation.option_payoff(
                #     option_strike,
                #     config_leg_obj.right,
                #     config_leg_obj.action,
                #     1,
                #     float(underlying_strike_price),
                #     int(instrument_object_for_leg_prem.multiplier),
                #     theoretical_premimum,
                # )

            # print(f"Leg PayOff: {leg_payoff} Strike: {option_strike} Premium: {leg_premium}")
            combination_payoff += leg_payoff
            combination_premium_received += leg_premium_received
        return combination_payoff, combination_premium_received


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

    
