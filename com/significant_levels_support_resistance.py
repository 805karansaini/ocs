"""
Created on 22-May-2023

@author: Karan
"""

import pandas as pd
import numpy as np
import bisect
from collections import Counter
import math
from com.variables import *


# To get support and restance price
def get_support_and_resitance_from_significant_levels(
    significant_lvl_dict, current_buy_price, current_sell_price
):
    # significant_lvl_dict consists of all signifact levels sorted in highest hit percentage to lowest hit percentage
    support = "N/A"
    resistance = "N/A"

    # Iterate over the significant_lvl_dict and find support and resistance.
    for price_lvl, hit_percent in significant_lvl_dict.items():
        # Resistance with highest hit percentage
        if (
            (current_buy_price != None)
            and (price_lvl > current_buy_price)
            and (resistance == "N/A")
        ):
            resistance = price_lvl

        # Support with highest hit percentage
        if (
            (current_sell_price != None)
            and (price_lvl < current_sell_price)
            and (support == "N/A")
        ):
            support = price_lvl

        # Break if we have have both support and resistance
        if (resistance != "N/A") and (support != "N/A"):
            break

    # If no such key exists, return None.
    return (resistance, support)


# Method to calculate support and resistance in rnage
def get_support_and_resitance_in_range_from_significant_levels(
    significant_lvl_dict, current_buy_price, current_sell_price
):
    # significant_lvl_dict consists of all signifact levels sorted in highest hit percentage to lowest hit percentage
    support = "N/A"
    resistance = "N/A"

    # Iterate over the significant_lvl_dict and find support and resistance.
    for price_lvl, hit_percent in significant_lvl_dict.items():
        # Resistance with highest hit percentage
        if (
            (current_buy_price != None)
            and (price_lvl > current_buy_price)
            and (resistance == "N/A")
        ):
            resistance = price_lvl

        # Support with highest hit percentage
        if (
            (current_sell_price != None)
            and (price_lvl < current_sell_price)
            and (support == "N/A")
        ):
            support = price_lvl

        # Break if we have have both support and resistance
        if (resistance != "N/A") and (support != "N/A"):
            break

    # If no such key exists, return None.
    return (resistance, support)


# Function to calculate significance levels
def calc_signficant_levels_v1(candles, offset_percent, number_of_levels):
    # Finding total no of candles
    num_candles = len(candles[1])

    # Merging all open and close values in single list
    all_candle_prices = candles[0] + candles[1]

    # Init Min, Max Price
    min_price, max_price = 10**10, -(10**10)

    # Calculating the min max prices
    for candle_price in all_candle_prices:
        if candle_price < min_price:
            min_price = candle_price
        if candle_price > max_price:
            max_price = candle_price

    # Creating the counter of how many times values appear in the candle data
    price_counter = Counter(all_candle_prices)

    # Calculating range between minimum and maximum value
    price_range_abs = max_price - min_price

    # Offset value
    # offset = price_range_abs * offset_percent
    offset = offset_percent

    # Calculating difference between two consecutive value levels
    level_gap = round((price_range_abs / number_of_levels), 2)

    # Handle case of level gap being too low and close to 0
    if level_gap == 0:
        level_gap = 0.1

    # Initializing dictionary that will contain the levle and its hits counter
    dict_value_levels = {}

    # Making list of unique values from all values available and sorting it
    all_candle_prices_set = sorted(list(set(all_candle_prices)))

    # Iterating over the price, and the computing the levels that are hit by the price and increasing the hit counter of the level
    for price in all_candle_prices_set:
        # Defining range for value level
        min_allowed_price_for_level = price - offset
        max_allowed_price_for_level = price + offset

        # Getting index range of sub-list form all values containing values present in range of value level
        lower_index = math.ceil((min_allowed_price_for_level - min_price) / level_gap)
        higher_index = math.floor((max_allowed_price_for_level - min_price) / level_gap)

        # Increase the hit counter
        if lower_index <= higher_index:
            for indx in range(lower_index, higher_index + 1):
                price_level = round(min_price + (level_gap * indx), 2)

                if price_level in dict_value_levels:
                    dict_value_levels[price_level] += price_counter[price]
                else:
                    dict_value_levels[price_level] = price_counter[price]

    # Sorting dictionary
    dict_value_levels = dict(
        sorted(dict_value_levels.items(), key=lambda item: item[1], reverse=True)
    )

    # Converting matches in percentage
    for key in dict_value_levels:
        dict_value_levels[key] = (dict_value_levels[key] / num_candles) * 100

    return dict_value_levels


# Function to calculate significance levels
def calc_signficant_levels(
    candles,
    number_of_levels=99,
    flag_in_range=False,
    unique_id=None,
    combo_obj=None,
):
    # Candles = [], [] list of open and close

    try:
        # Finding total no of candles
        num_candles = len(candles[1])

        # Merging all open and close values in single list
        all_candle_prices = candles[0] + candles[1]

        # Init Min, Max Price
        min_price, max_price = 10**10, -(10**10)

        # Check if flag is true
        if flag_in_range:
            try:
                if unique_id > 0:
                    # Make it available in variables
                    avg_price_combo = (
                        variables.unique_id_to_prices_dict[unique_id]["BUY"]
                        + variables.unique_id_to_prices_dict[unique_id]["SELL"]
                    ) / 2

                else:
                    avg_price_combo = None

                    if combo_obj is not None:
                        all_legs = combo_obj.buy_legs + combo_obj.sell_legs

                        for leg_obj in all_legs:
                            req_id = variables.con_id_to_req_id_dict[leg_obj.con_id]
                            bid, ask = (
                                variables.bid_price[req_id],
                                variables.ask_price[req_id],
                            )
                            avg_price_combo = (ask + bid) / 2

                min_price = avg_price_combo * (
                    1 - variables.support_resistance_range_percent
                )

                max_price = avg_price_combo * (
                    1 + variables.support_resistance_range_percent
                )

            except Exception as e:
                min_price = "N/A"
                max_price = "N/A"

        else:
            # Calculating the min max prices
            for candle_price in all_candle_prices:
                if candle_price < min_price:
                    min_price = candle_price
                if candle_price > max_price:
                    max_price = candle_price

        # Creating the counter of how many times values appear in the candle data
        price_counter = Counter(all_candle_prices)

        # Calculating range between minimum and maximum value
        price_range_abs = max_price - min_price

        # Offset value
        offset = (price_range_abs / number_of_levels) / 2

        # Calculating difference between two consecutive value levels
        # Handle case of level gap being too low and close to 0
        level_gap = max(round((price_range_abs / number_of_levels), 2), 0.1)

        # Initializing dictionary that will contain the levle and its hits counter
        dict_value_levels = {}

        # Making list of unique values from all values available and sorting it
        all_candle_prices_set = sorted(list(set(all_candle_prices)))

        # Iterating over the price, and the computing the levels that are hit by the price and increasing the hit counter of the level
        for price in all_candle_prices_set:
            # Defining range for value level
            min_allowed_price_for_level = price - offset
            max_allowed_price_for_level = price + offset

            # Getting index range of sub-list form all values containing values present in range of value level
            lower_index = math.ceil(
                (min_allowed_price_for_level - min_price) / level_gap
            )
            higher_index = math.floor(
                (max_allowed_price_for_level - min_price) / level_gap
            )

            # Increase the hit counter
            if lower_index <= higher_index:
                for indx in range(lower_index, higher_index + 1):
                    price_level = round(min_price + (level_gap * indx), 2)

                    if price_level in dict_value_levels:
                        dict_value_levels[price_level] += price_counter[price]
                    else:
                        dict_value_levels[price_level] = price_counter[price]

        # Sorting dictionary
        dict_value_levels = dict(
            sorted(dict_value_levels.items(), key=lambda item: item[1], reverse=True)
        )

        dict_percentage_for_value_levels = {}

        # Converting matches in percentage
        for key in dict_value_levels:
            dict_percentage_for_value_levels[key] = (
                dict_value_levels[key] / num_candles
            ) * 100

        return dict_percentage_for_value_levels, dict_value_levels

    except Exception as e:
        return None, None
