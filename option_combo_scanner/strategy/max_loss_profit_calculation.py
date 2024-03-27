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

        for symbol, strike, delta, conid, expiry, bid, ask, iv in combination:
            if symbol in grouped_tuples:
                grouped_tuples[symbol].append((symbol, strike, delta, conid, expiry, bid, ask, iv))
            else:
                grouped_tuples[symbol] = [(symbol, strike, delta, conid, expiry, bid, ask, iv)]

        return list(grouped_tuples.values())
    
    # find the closest expiry for the group combination
    @staticmethod
    def find_closest_expiry(group_combinations):
        closest_expiry_list = []
        for group_combination in group_combinations:
            min_expiry = 99999999
            for symbol, strike, delta, _, expiry, _, _, _ in group_combination:
                if int(expiry) < min_expiry:
                    min_expiry = int(expiry)
            closest_expiry_list.append(str(min_expiry))
        return closest_expiry_list

    @staticmethod
    def calcluate_maxpnl(combination, list_of_config_leg_object):
        total_grp_max_profit = total_grp_max_loss = 0
        # Group Combination based on same uderlying
        group_combinations = MaxPNLCalculation.create_group_same_und(combination)
        # get the list of closest expiry for the groups
        list_of_closest_expiry = MaxPNLCalculation.find_closest_expiry(group_combinations)

        # iterate over the group to get payoff for group combination
        for group_combination, closest_expiry in zip(group_combinations, list_of_closest_expiry):
            max_loss, max_profit = MaxPNLCalculation.get_combination_max_loss_and_max_profit(
                    list_of_legs_tuple=group_combination,
                    list_of_config_leg_objects=list_of_config_leg_object,
                    closest_expiry = closest_expiry,
                )
            
            total_grp_max_profit += (max_profit)
            total_grp_max_loss += (max_loss)
        return total_grp_max_profit, total_grp_max_loss
    
    @staticmethod
    def get_combination_max_loss_and_max_profit(list_of_legs_tuple, list_of_config_leg_objects, closest_expiry):
        max_profit = float("-inf")
        max_loss = float("inf")

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
        
            # Get the combination payoff for the strike of current leg
            combo_pay_off_for_current_strike, combination_premium_received = MaxPNLCalculation.get_combination_payoff(
                list_of_legs_tuple,
                list_of_config_leg_objects,
                leg_tuple[1],
                closest_expiry,
            )
            combo_pay_off_for_current_strike = round(combo_pay_off_for_current_strike)

            # Max Profit is max of (Payoff Strike1, PayoffStrike2...)
            max_profit = max(max_profit, combo_pay_off_for_current_strike)
            max_loss = min(max_loss, combo_pay_off_for_current_strike)

            # Get the payoff for left strike 0
            strike_zero_payoff, combination_premium_received = MaxPNLCalculation.get_combination_payoff(
                list_of_legs_tuple,
                list_of_config_leg_objects,
                0,
                closest_expiry,
            )
            # Get the payoff for left + 1
            strike_one_payoff, combination_premium_received = MaxPNLCalculation.get_combination_payoff(
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
                max_strike_right_payoff, combination_premium_received = MaxPNLCalculation.get_combination_payoff(
                    list_of_legs_tuple,
                    list_of_config_leg_objects,
                    list_of_legs_tuple[i][1] * 2,
                    closest_expiry,
                )
                # Get payoff for right - 1
                max_strike_right_one_payoff, combination_premium_received = MaxPNLCalculation.get_combination_payoff(
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

        # Final Premium
        max_profit += round(combination_premium_received, 2)
        max_loss += round(combination_premium_received, 2)

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
            symbol, option_strike,_, _, leg_expiry, bid, ask, leg_iv = leg
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
                theoretical_premimum = Utils.get_theoretical_premium(underlying_strike_price, strategy_variables.riskfree_rate1, 0, time_to_expiration, option_strike, leg_iv, config_leg_obj.right)                
                # calculate leg payoff for case where leg expiry is later than closest expiry
                leg_payoff, leg_premium_received = MaxPNLCalculation.option_payoff(
                    option_strike,
                    config_leg_obj.right,
                    config_leg_obj.action,
                    1,
                    float(underlying_strike_price),
                    int(instrument_object_for_leg_prem.multiplier),
                    theoretical_premimum,
                )

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

    
