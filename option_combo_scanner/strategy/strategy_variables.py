import configparser
import datetime
import threading
from typing import List, Tuple

import pandas as pd

# Read the config file
config = configparser.ConfigParser()
config.read("config.ini")

# Settings from config file
execution_engine_config = config["ExecutionEngine"]
time_zone_config = config["TimeZone"]


class StrategyVariables:
    """
    Class Variables for the strategy
    will be used to store variables that are used across different modules
    mainly the GUI and the monitoring and the execution modules
    """

    map_instrument_id_to_instrument_object = {}
    # not using it anywhere, aryan created this but since there will be a single config in system, hence we are usign 'config_object'
    map_config_id_to_config_object = {}
    map_configleg_id_to_config_object = {}
    map_indicator_id_to_indicator_object = {}
    map_instrument_to_indicator_id = {}
    config_object = None
    nextorderId = None
    hv_look_back_days = 14
    # Input for delta
    delta_d1_indicator_input = 0.25
    delta_d2_indicator_input = 0.50
    riskfree_rate1 = 0.04
    avg_iv_lookback_days = 14  # Days  Average(AvgIV_0Day... AvgIV_NDay)

    # For HV # Take candle size from the
    user_input_bar_size_historical_volatility = 1  # Hours
    user_input_lookback_days_historical_volatility = 14  # Days
    user_input_average_historical_volatility_days = 14  # Days

    user_input_lookback_days_implied_volatility = 14  # Days

    bar_size_historical_volatility = f"{user_input_bar_size_historical_volatility} hour"
    lookback_days_historical_volatility = f"{user_input_lookback_days_historical_volatility} D"
    duration_size_historical_volatility = (
        f"{user_input_average_historical_volatility_days  + user_input_lookback_days_historical_volatility - 1} D"
    )
    flag_hv_daily = True  # TODO Remove it

    # For Option Change
    bar_size_for_option_change_cal = "1 hour"

    # If the flag is False it will calcluate for all put-call strike otherwise for speicfic deltas
    flag_put_call_indicator_based_on_selected_deltas_only = False

    # Put Call Volume Variable
    put_call_volume_lookback_days = "14 D"
    put_call_volume_bar_size = "4 hours"

    # Flag if we want to calculate the put call volume for all contracts or only for the selected deltas
    flag_put_call_volume_for_all_contracts = False

    list_of_percent_for_impact_calcluation = sorted(set([2, -2, 5, -5, 10, -10, 20, -20]))

    ###########################
    # Scanner
    ###########################
    flag_force_restart_scanner = False
    rescan_time_in_seconds = 10 * 60
    
    # Indicator Cache time in seconds for the scanner
    indicator_cache_time_in_seconds = 60 * 60

    # Variables used in filtering in range 0 to 1 threshold
    flag_enable_filter_based_delta_threshold = True
    min_delta_threshold = 0.009
    max_delta_threshold = 0.990

        
    flag_store_csv_files = True
    o_c_s_folder_path = fr"..\OCSFiles"
    batch_size = 120
    batch_size_historical_data = 10
    
    # Flag if we want the option indicator in % chng
    flag_chng_in_opt_price_in_percentage = False


    ###########################
    # Variable to map combo id to combination object
    map_combo_id_to_scanner_combination_object = {}

    screen = None
    standard_currency_for_the_app = "USD"
    scanner_combination_table_sort_by_column = {"Combo ID": False}

    # Timezone object for the target time zone
    target_time_zone = time_zone_config["target_timezone"]

    # Order Execution Lock
    order_execution_lock = threading.Lock()

    # Set of symbols for which the order execution is sent only used inside the lock/critical section
    set_symbols_for_which_order_execution_sent = set()
    map_symbol_to_sent_completed_execution = {}

    map_con_id_to_contract = {}
    map_unique_id_to_order_preset_obj = {}
    list_of_unique_ids_for_which_entry_order_is_pending: List[Tuple[int, int]] = []

    # Scanner Combination Table Column for df
    scanner_combination_table_columns = [
        "Combo ID",
        "Instrument ID",
        "Description",
        "#Legs",
        "Combo Net Delta",
        "Max Profit",
        "Max Loss",
        "Max Profit/Loss Ratio",
    ]
    # scanner combo table dataframe
    scanner_combo_table_df = pd.DataFrame(columns=scanner_combination_table_columns)


    # For View detials of scanner combo
    leg_columns_combo_detail_gui = [
        "Action",
        "Symbol",
        "SecType",
        "Exchange",
        "Currency",
        "#Lots",
        "Expiry",
        "Strike",
        "Right",
        "Multiplier",
        "ConID",
        "Primary Exchange",
        "Trading Class",
    ]

    
    # Define column names based on the attributes of the Indicator class
    indicator_columns = [
        "indicator_id",
        "instrument_id",
        "underlying_conid",
        "symbol",
        "sec_type",
        "expiry",
        "multiplier",
        "exchange",
        "trading_class",
        "current_underlying_hv_value",
        "average_underlying_hv_over_n_days",
        "absoulte_change_in_underlying_over_n_days",
        "percentage_change_in_underlying_over_n_days",
        "current_iv_d1",
        "current_iv_d2",
        "current_avg_iv",
        "absolute_change_in_avg_iv_since_yesterday",
        "percentage_change_in_avg_iv_since_yesterday",
        "avg_iv_over_n_days",
        "current_rr_d1",
        "current_rr_d2",
        "percentage_change_in_rr_since_yesterday_d1",
        "percentage_change_in_rr_since_yesterday_d2",
        "percentage_change_in_rr_since_14_day_d1",
        "percentage_change_in_rr_since_14_day_d2",
        "max_pain_strike",
        "min_pain_strike",
        "oi_support_strike",
        "oi_resistance_strike",
        "put_call_volume_ratio_current_day",
        "put_call_volume_ratio_average_over_n_days",
        "absolute_pc_change_since_yesterday",
        "current_hv_minus_iv",
        "pc_change_iv_change",
        "underlying_chg_by_call_opt_price_since_yesterday_d1",
        "underlying_chg_by_call_opt_price_since_yesterday_d2",
        "underlying_chg_by_put_opt_price_since_yesterday_d1",
        "underlying_chg_by_put_opt_price_since_yesterday_d2",
        "underlying_chg_by_call_opt_price_since_nth_day_d1",
        "underlying_chg_by_call_opt_price_since_nth_day_d2",
        "underlying_chg_by_put_opt_price_since_nth_day_d1",
        "underlying_chg_by_put_opt_price_since_nth_day_d2",
    ]


















    # Not Creating the DF for the Indicators
    # scanner_indicator_table_columns = [
    #     "Indicator ID",
    #     "Instrument ID",
    #     "Symbol",
    #     "SecType",
    #     "Expiry",
    #     "current_underlying_hv_value",
    #     "average_underlying_hv_over_n_days",
    #     "current_iv_d1",
    #     "current_iv_d2",
    #     "current_avg_iv",
    #     "absolute_change_in_avg_iv_since_yesterday",
    #     "percentage_change_in_avg_iv_since_yesterday",
    #     "current_rr_d1",
    #     "current_rr_d2",
    #     "percentage_change_in_rr_since_14_day_d1",
    #     "percentage_change_in_rr_since_14_day_d2",
    #     "percentage_change_in_rr_since_yesterday_d1",
    #     "percentage_change_in_rr_since_yesterday_d2",
    #     "max_pain_strike",
    #     "min_pain_strike",
    #     "support_strike",
    #     "resistance_strike",
    #     "put_call_volume_ratio_current_day",
    #     "put_call_volume_ratio_average_over_n_days",
    #     "pc_change_since_yesterday",
    #     "absoulte_change_in_underlying_over_n_days",
    #     "percentage_change_in_underlying_over_n_days",
    #     # "hv",
    #     # "iv_d1",
    #     # "iv_d2",
    #     # "avg_iv",
    #     # "rr_d1",
    #     # "rr_d2",
    #     # "avg_iv_avg_14d",
    #     # "change_rr_d1_1D",
    #     # "change_rr_d2_1D",
    #     # "change_rr_d1_14D",
    #     # "change_rr_d2_14D",
    #     # "hv_14d_avg_14d",
    #     # "hv_14d_avg_iv",
    #     # "open_interest_support",
    #     # "open_interest_resistance",
    #     # "pc_change",
    #     # "put_call_ratio_avg",
    #     # "put_call_ratio_current",
    #     # "Change_underlying_options_price_today",
    #     # "chg_uderlying_opt_price_14d",
    #     # "change_in_iv",
    #     # "pc_change_iv_change",
    #     # "min_pain",
    #     # "max_pain",
    # ]
    # # scanner combo table dataframe
    # # scanner_indicator_table_df = pd.DataFrame(columns=scanner_indicator_table_columns)
