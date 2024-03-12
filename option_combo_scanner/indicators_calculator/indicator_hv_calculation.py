import pandas as pd
import numpy as np
import bisect
from collections import Counter
import os
from com.variables import *
from option_combo_scanner.strategy.strategy_variables import StrategyVariables
from option_combo_scanner.strategy.utilities import StrategyUtils


# Global function to calculate Historic volatility using all 4 methods
def calculate_hv(
    conid,
    hv_method,
    combination_price_dataframe,
    avg_price_combo,
):

    try:
        # Redirecting to Standard deviation of closing prices method
        if hv_method.name == "STANDARD_DEVIATION":
            return calculate_standard_deviation(
                conid,
                combination_price_dataframe,
            )

        # Redirecting to Average True Range method
        elif hv_method.name == "NATR":
            calculated_atr = calculate_combo_atr(
                conid,
                combination_price_dataframe,
                "Historical Volatility",
            )
            normalised_atr = round((calculated_atr / avg_price_combo) * 100, 2)
            return normalised_atr

        # Redirecting to Parkinsons Range without gap method
        elif hv_method.name == "PARKINSON_WITHOUT_GAP":
            return calculate_parkinson_range_without_gaps(
                conid,
                combination_price_dataframe,
            )

        # Redirecting to Parkinsons Range with gaps method
        elif hv_method.name == "PARKINSON_WITH_GAP":
            return calculate_parkinson_range_with_gaps(
                conid,
                combination_price_dataframe,
            )

        else:
            print(f"Wrong HV Method was given... Exiting")
            
    except Exception as e:

        if variables.flag_debug_mode:
            print(f"Inside calculate HV, error is {e}")

        return "N/A"


# calculating standard deviation using numpy
def calculate_standard_deviation(
    conid,
    combination_price_dataframe,
):

    # Calculating candle return for the long term candle(Regulary HV Calcultaions)
    combination_price_dataframe["Candle Return"] = combination_price_dataframe[
        "Combination Close"
    ].pct_change()

    # Calculating standard Deviation
    standard_dev_result = round(
        np.std(combination_price_dataframe["Candle Return"]) * 100, 8
    )
    
    # TODO - REMOVE IT
    # Print the DataFrame using tabulate
    # print(combination_price_dataframe.to_string())
    # print(tabulate.tabulate(combination_price_dataframe, headers="keys", tablefmt="psql"))

    # Save DF to CSV File (HV) Export data-frame to csv file
    # if flag is True Save CSV file
    if StrategyVariables.flag_store_csv_files:
        folder_name = "OCS_HV"
        file_name = rf"Standard deviation_HV_Unique_id_{conid}"

        StrategyUtils.save_option_combo_scanner_csv_file(combination_price_dataframe, folder_name, file_name)

    # Using standard deviation for relative change among prices
    return standard_dev_result


# Calculating parkison's range formula with given values
def calculate_parkinson_range_formula_calculations(high_prices, low_prices):

    # Converting list to numpy array
    high_prices, low_prices = np.array(high_prices), np.array(low_prices)

    # Getting values for column parkinson_volatility_term
    parkinson_volatility_term = np.log(abs(high_prices) + 1) * np.copysign(
        1, high_prices
    ) - np.log(abs(low_prices) + 1) * np.copysign(1, low_prices)

    # Getting values for column parkinson_volatility_term_square
    parkinson_volatility_term_square = parkinson_volatility_term**2

    # Check if the ndarray is empty
    if parkinson_volatility_term_square.size == 0:

        parkinson_range = "N/A"

    else:

        # Applying parkinson's range formula
        parkinson_range = np.sqrt(
            (1 / (4 * np.log(2))) * np.mean(parkinson_volatility_term_square)
        )

        parkinson_range = round(parkinson_range * 100, 2)

    return (
        parkinson_range,
        list(parkinson_volatility_term),
        list(parkinson_volatility_term_square),
    )


# Calculate parkison's range formula without gaps
# high_prices, low_prices):
def calculate_parkinson_range_without_gaps(
    conid,
    combination_price_dataframe,
):

    # assigning the column name for open and close data from dataframe
    # TODO ARYAN
    open_price_column_name = "Combination Open"
    close_price_column_name = "Combination Close"

    # If we are calculating the Parksionson's range without gaps for Intraday values and for individual legs, columns will be High x, low x
    low_price_column_name = "Combination Low"
    high_price_column_name = "Combination High"

    # Comnbination High
    combination_price_dataframe[
        high_price_column_name
    ] = combination_price_dataframe.apply(
        lambda row: max(
            row[open_price_column_name],
            row[close_price_column_name],
        ),
        axis=1,
    )

    # Combination Low
    combination_price_dataframe[
        low_price_column_name
    ] = combination_price_dataframe.apply(
        lambda row: min(
            row[open_price_column_name],
            row[close_price_column_name],
        ),
        axis=1,
    )

    # Applying parkinson's range formula
    (
        parkinson_range_result,
        parkinson_volatility_term,
        parkinson_volatility_term_square,
    ) = calculate_parkinson_range_formula_calculations(
        combination_price_dataframe[high_price_column_name],
        combination_price_dataframe[low_price_column_name],
    )

    # If we are calculating the Parksionson's range without gaps for Intraday values and for individual legs,
    #  columns will be PV_term x, PV_Term_Sq x
    # TODO ARYAN
    # assigining the column name for pv_term and pv_term sq
    pv_term_values_column_name = "PV_term"
    pv_term_sq_values_column_name = "PV_Term_Sq"

    # Adding 2 columns in data frame namely parkinson_volatility_term and parkinson_volatility_term_square
    combination_price_dataframe[pv_term_values_column_name] = parkinson_volatility_term
    combination_price_dataframe[
        pv_term_sq_values_column_name
    ] = parkinson_volatility_term_square
    
    # If Flag Save OCS Files 
    if StrategyVariables.flag_store_csv_files:
        folder_name = "OCS_HV"
        file_name = rf"parkinson_volatility_HV_Unique_id_{conid}"

        StrategyUtils.save_option_combo_scanner_csv_file(combination_price_dataframe, folder_name, file_name)

    return parkinson_range_result


# Determining Combination high with gaps from csv
def get_combination_high_with_gaps(open_prices, close_prices):

    return [
        max(open_prices[index], close_prices[index], close_prices[index - 1])
        for index in range(1, len(open_prices))
    ]


# Determining Combination low with gaps from csv
def get_combination_low_with_gaps(open_prices, close_prices):

    return [
        min(open_prices[index], close_prices[index], close_prices[index - 1])
        for index in range(1, len(open_prices))
    ]


# Calculating Parkinson's range with gaps with modified values of high and low
def calculate_parkinson_range_with_gaps(
    conid,
    combination_price_dataframe,
):

    # If we are calculating the Parksionson's range with gaps for Intraday values and for individual legs, columns will be Open x, Close x
    # TODO ARYAN COMMMENT

    open_price_column_name = "Combination Open"
    close_price_column_name = "Combination Close"

    # If we are calculating the Parksionson's range with gaps for Intraday values and for individual legs, columns will be High x, low x
    # TODO ARYAN COMMMENT
    low_price_column_name = "Combination Low with Gaps"
    high_price_column_name = "Combination High with Gaps"

    # Determining Combination high with gaps from csv
    high_prices_with_gaps = get_combination_high_with_gaps(
        combination_price_dataframe[open_price_column_name],
        combination_price_dataframe[close_price_column_name],
    )

    # Determining Combination low with gaps from csv
    low_prices_with_gaps = get_combination_low_with_gaps(
        combination_price_dataframe[open_price_column_name],
        combination_price_dataframe[close_price_column_name],
    )

    # Applying parkinson's range formula
    (
        parkinson_range_result,
        parkinson_volatility_term,
        parkinson_volatility_term_square,
    ) = calculate_parkinson_range_formula_calculations(
        high_prices_with_gaps, low_prices_with_gaps
    )

    # Adding nan value at index 0 since length of candle return column will be 1 shorter than prices value
    high_prices_with_gaps.insert(0, np.nan)
    low_prices_with_gaps.insert(0, np.nan)
    parkinson_volatility_term.insert(0, np.nan)
    parkinson_volatility_term_square.insert(0, np.nan)

    # Adding 2 columns in data frame namely Combination High and Combination Low with gaps
    combination_price_dataframe.insert(
        len(combination_price_dataframe.columns),
        high_price_column_name,
        high_prices_with_gaps,
    )
    combination_price_dataframe.insert(
        len(combination_price_dataframe.columns),
        low_price_column_name,
        low_prices_with_gaps,
    )

    # If we are calculating the Parksionson's range with gaps for Intraday values and for individual legs, columns will be PV_term x, PV_Term_Sq x
    # TODO ARYAN COMMMENT
    pv_term_values_column_name = "PV_term"
    pv_term_sq_values_column_name = "PV_Term_Sq"

    # Adding 2 columns in data frame namely parkinson_volatility_term and parkinson_volatility_term_square
    combination_price_dataframe.insert(
        len(combination_price_dataframe.columns),
        pv_term_values_column_name,
        parkinson_volatility_term,
    )
    combination_price_dataframe.insert(
        len(combination_price_dataframe.columns),
        pv_term_sq_values_column_name,
        parkinson_volatility_term_square,
    )
    
    # If Flag Save OCS Files 
    if StrategyVariables.flag_store_csv_files:
        folder_name = "OCS_HV"
        file_name = rf"parkinson_volatility_with_gaps_HV_Unique_id_{conid}"

        StrategyUtils.save_option_combo_scanner_csv_file(combination_price_dataframe, folder_name, file_name)

    return parkinson_range_result


# Method to calculate ATR
def calculate_combo_atr(
    conid,
    combo_daily_open_close_df,
    atr_type="Historical Volatility",
):

    # Take 'K' Data Points
    k = len(combo_daily_open_close_df)

    # Calculate TR
    combo_daily_open_close_df["TR"] = 0.0

    # TODO - COmmment ARYAN
    # If we are calculating the ATR for Intraday values and for individual legs, columns will be Open x, Close x
    open_price_column_name = "Combination Open"
    close_price_column_name = "Combination Close"

    for i in range(len(combo_daily_open_close_df)):

        if i == 0:
            combo_daily_open_close_df.loc[i, "TR"] = max(
                combo_daily_open_close_df.loc[i, open_price_column_name],
                combo_daily_open_close_df.loc[i, close_price_column_name],
            ) - min(
                combo_daily_open_close_df.loc[i, open_price_column_name],
                combo_daily_open_close_df.loc[i, close_price_column_name],
            )
        else:
            combo_daily_open_close_df.loc[i, "TR"] = max(
                combo_daily_open_close_df.loc[i, open_price_column_name],
                combo_daily_open_close_df.loc[i, close_price_column_name],
                combo_daily_open_close_df.loc[i - 1, close_price_column_name],
            ) - min(
                combo_daily_open_close_df.loc[i, open_price_column_name],
                combo_daily_open_close_df.loc[i, close_price_column_name],
                combo_daily_open_close_df.loc[i - 1, close_price_column_name],
            )

    # Calculate ATR
    combo_daily_open_close_df["ATR"] = 0.0
    for i in range(len(combo_daily_open_close_df)):
        if i == 0:
            combo_daily_open_close_df.loc[i, "ATR"] = combo_daily_open_close_df.loc[
                i, "TR"
            ]
        else:
            combo_daily_open_close_df.loc[i, "ATR"] = (
                combo_daily_open_close_df.loc[i - 1, "ATR"] * (k - 1)
                + combo_daily_open_close_df.loc[i, "TR"]
            ) / k

    # If Flag Save OCS Files 
    if StrategyVariables.flag_store_csv_files and atr_type == "Historical Volatility":
        folder_name = "OCS_HV"
        file_name = rf"ATR_HV_Unique_id_{conid}"

        StrategyUtils.save_option_combo_scanner_csv_file(combo_daily_open_close_df, folder_name, file_name)


    # ATR
    try:
        atr = combo_daily_open_close_df.iloc[-1]["ATR"]
    except Exception as e:

        if variables.flag_debug_mode:
            # Print to console
            print(f"Unable to calculate ATR")

        atr = None

    return atr


# Method to calculate ATR for positive and negative candles
def calculate_combo_atr_for_positive_negative_candles(combo_daily_open_close_df):
    # Take 'K' Data Points
    k = len(combo_daily_open_close_df)

    # reset index
    combo_daily_open_close_df = combo_daily_open_close_df.reset_index(drop=True)

    # Calculate TR
    combo_daily_open_close_df["TR"] = 0.0

    # column names
    open_price_column_name = "Combination Open"
    close_price_column_name = "Combination Close"
    previous_close_price_column_name = "Previous Close"

    for i in range(len(combo_daily_open_close_df)):

        if i == 0:
            combo_daily_open_close_df.loc[i, "TR"] = max(
                combo_daily_open_close_df.loc[i, open_price_column_name],
                combo_daily_open_close_df.loc[i, close_price_column_name],
            ) - min(
                combo_daily_open_close_df.loc[i, open_price_column_name],
                combo_daily_open_close_df.loc[i, close_price_column_name],
            )
        else:
            combo_daily_open_close_df.loc[i, "TR"] = max(
                combo_daily_open_close_df.loc[i, open_price_column_name],
                combo_daily_open_close_df.loc[i, close_price_column_name],
                combo_daily_open_close_df.loc[i, previous_close_price_column_name],
            ) - min(
                combo_daily_open_close_df.loc[i, open_price_column_name],
                combo_daily_open_close_df.loc[i, close_price_column_name],
                combo_daily_open_close_df.loc[i, previous_close_price_column_name],
            )

    # Calculate ATR
    combo_daily_open_close_df["ATR"] = 0.0
    for i in range(len(combo_daily_open_close_df)):
        if i == 0:
            combo_daily_open_close_df.loc[i, "ATR"] = combo_daily_open_close_df.loc[
                i, "TR"
            ]
        else:
            combo_daily_open_close_df.loc[i, "ATR"] = (
                combo_daily_open_close_df.loc[i - 1, "ATR"] * (k - 1)
                + combo_daily_open_close_df.loc[i, "TR"]
            ) / k

    # ATR
    try:
        atr = combo_daily_open_close_df.iloc[-1]["ATR"]
    except Exception as e:
        # Print to console

        if variables.flag_debug_mode:
            print(f"Unable to calculate ATR")

        atr = None

    return atr


# Gets the timestamp of the lowest point and highest point of price (intraday). - Column 5
def get_timestamp_of_lowest_and_highest_point_of_price(latest_day_dataframe):
    """
    Gets the timestamp of the lowest point and highest point of price (intraday).
    """

    lowest_price = 10**12
    high_price = -(10**12)

    # Retrieve timestamps
    lowest_timestamp = "N/A"
    highest_timestamp = "N/A"

    try:
        for _, row in latest_day_dataframe.iterrows():

            open_price = row["Combination Open"]
            close_price = row["Combination Close"]
            date_time_stamp = row["Time"]

            if lowest_price > close_price:
                lowest_timestamp = date_time_stamp
                lowest_price = close_price

            if high_price < close_price:
                highest_timestamp = date_time_stamp
                high_price = close_price
    except Exception as e:

        if variables.flag_debug_mode:
            print(e)

    lowest_timestamp = lowest_timestamp.strftime("%H:%M:%S")
    highest_timestamp = highest_timestamp.strftime("%H:%M:%S")

    return lowest_timestamp, highest_timestamp


# Sum of abs(Change) for each period since the market opened
def sum_of_abs_changes(open_prices, close_prices):
    """
    Calculates the sum of the absolute changes between adjacent values in a list.

    Args:
      list: A list of values.

    Returns:
      The sum of the absolute changes.
    """
    # Intializing variable to store sum of absolute changes
    sum_of_abs_change = 0

    # Calculating sum of absolute changes by getting difference between consecutive values and summing it up
    for i in range(1, len(open_prices)):
        try:
            change = abs(close_prices[i] / open_prices[i] - 1)
        except Exception as e:
            change = 0

        sum_of_abs_change += change

    return round(sum_of_abs_change, 4)


# Candle Volatility - Column 1
def calculate_candle_volatility(
    historical_volatility_of_the_combination,
    current_day_open_prices,
    current_day_close_prices,
    number_of_candles_since_day_open,
):

    # Calculating sum of absolute changes in prices since market opened
    sum_of_change_since_market_opened_on_candle_basis = sum_of_abs_changes(
        current_day_open_prices, current_day_close_prices
    )

    # Converting to percentage (x 100)
    sum_of_change_since_market_opened_on_candle_basis = (
        sum_of_change_since_market_opened_on_candle_basis * 100
    )

    return (
        historical_volatility_of_the_combination * number_of_candles_since_day_open
    ) - sum_of_change_since_market_opened_on_candle_basis
