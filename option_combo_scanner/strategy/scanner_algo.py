from functools import cache
import pandas as pd

from option_combo_scanner.strategy.strategy_variables import StrategyVariables


class ScannerAlgo:

    # def __init__(self):
    def __init__(self, config_obj, strike_and_delta_dataframe):
        self.config_obj = config_obj
        self.strike_and_delta_dataframe = strike_and_delta_dataframe

        # Filter the nan Values
        self.filter_dataframe()

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
        self.strike_and_delta_dataframe['Delta'] = self.strike_and_delta_dataframe['Delta'].abs()
        
        # Remove all the row that have delta less than min_delta_threshold
        if StrategyVariables.flag_enable_filter_based_delta_threshold:
            self.strike_and_delta_dataframe = self.strike_and_delta_dataframe[
                (self.strike_and_delta_dataframe['Delta'] > StrategyVariables.min_delta_threshold)]

            # Remove all the row that have delta higher than max_delta_threshold
            self.strike_and_delta_dataframe = self.strike_and_delta_dataframe[
                (self.strike_and_delta_dataframe['Delta'] < StrategyVariables.max_delta_threshold)]


    def filter_strikes(self, delta_range_low, delta_range_high):
        """
        Filters strikes based on the given delta_range_low and delta_range_high.

        Args:
            self: reference to the current instance of the class
            delta_range_low (float): Lower bound of the delta range
            delta_range_high (float): Upper bound of the delta range

        Returns:
            pandas.DataFrame: Filtered dataframe containing strikes within the given delta range
        """

        # Make a copy of the dataframe to avoid modifying the original dataframe
        filtered_dataframe = self.strike_and_delta_dataframe.copy()

        # Filter strikes based on delta_range_low and delta_range_high
        filtered_dataframe = filtered_dataframe[
            (filtered_dataframe["Delta"] >= delta_range_low)
            & (filtered_dataframe["Delta"] <= delta_range_high)
        ]

        # Return the filtered dataframe
        return list(filtered_dataframe[['Strike', 'Delta', 'ConId']].itertuples(index=False, name=None))
        return list(filtered_dataframe)
    
    @cache
    def generate_combinations(
        self, remaining_no_of_legs, range_low, range_high
    ):  
        """
        #   2 
        #   0.5 to 0.7,  
        #   -0.1 to 0.2
        """
        # print("generate_combinations", remaining_no_of_legs, range_low, range_high)
        list_of_filter_legs = self.filter_strikes(range_low, range_high)

        list_of_partial_combination = []

        if remaining_no_of_legs == 0:
            for strike, strike_delta, con_id in list_of_filter_legs:
                list_of_partial_combination.append([(strike, strike_delta, con_id)])
        else:
            list_of_config_leg_object = self.config_obj.list_of_config_leg_object
            leg_object = list_of_config_leg_object[-remaining_no_of_legs]

            (leg_number, action, delta_range_min, delta_range_max) = (
                leg_object.get_config_leg_tuple_for_gui()
            )

            # print("-----")
            # print("Leg Object: ", leg_object)
            # print("-----")
            delta_range_min = float(delta_range_min) 
            delta_range_max = float(delta_range_max)
            
            for strike, strike_delta, con_id in list_of_filter_legs:

                new_range_low = strike_delta - delta_range_min
                new_range_high = strike_delta + delta_range_max
                
                list_of_strike_delta_and_con_id_tuple = self.generate_combinations(
                    remaining_no_of_legs - 1,
                    new_range_low,
                    new_range_high,
                )
                current_leg_strike_and_strike_delta = [(strike, strike_delta, con_id)]
                for next_legs_strike_delta_and_con_id in list_of_strike_delta_and_con_id_tuple:
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
    
    
    def run_scanner(self, remaining_no_of_legs,
            range_low,
            range_high,):
        
        list_of_combination = self.generate_combinations(
            remaining_no_of_legs,
            range_low,
            range_high,
        )
        
        # print("list_of_combination", list_of_combination)
        list_of_filter_combination = self.filter_list_of_combination(list_of_combination)
        list_of_filter_combination_without_dup = self.remove_duplicate_combo_different_order(list_of_filter_combination)
        
        return list_of_filter_combination_without_dup
