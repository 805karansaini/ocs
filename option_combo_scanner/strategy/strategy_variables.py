import configparser
import datetime
import threading
from typing import List, Tuple

import pandas as pd
from enum import Enum

# # Read the config file
config = configparser.ConfigParser()
config.read("option_scanner_user_inputs.ini")

# Settings from config file

time_zone_config = config["TimeZone"]


class MaxPNLEnum(Enum):
    ONE = 1
    GNE = 2

class StrategyVariables:
    """
    Class Variables for the strategy
    will be used to store variables that are used across different modules
    mainly the GUI and the monitoring and the execution modules
    """

    parser = configparser.ConfigParser()
    parser.read("option_scanner_user_inputs.ini")

    map_instrument_id_to_instrument_object = {}
    # not using it anywhere, aryan created this but since there will be a single config in system, hence we are usign 'config_object'
    map_config_id_to_config_object = {}
    map_configleg_id_to_config_object = {}
    map_indicator_id_to_indicator_object = {}
    map_instrument_to_indicator_id = {}
    config_object = None
    nextorderId = None

    ibkr_tws_host = parser.get("USER INPUTS", "ibkr_tws_host")
    ibkr_tws_port = parser.getint("USER INPUTS", "ibkr_tws_port")
    ibkr_tws_connection_id = parser.getint("USER INPUTS", "ibkr_tws_connection_id")

    # User Input for the calc. mode in in the max PnL cacl
    calculation_mode_for_combination_max_pnl = MaxPNLEnum.GNE

    # Input for delta
    delta_d1_indicator_input = parser.getfloat("USER INPUTS", "delta_d1_indicator_input")
    delta_d2_indicator_input = parser.getfloat("USER INPUTS", "delta_d2_indicator_input")
    riskfree_rate1 = parser.getfloat("USER INPUTS", "riskfree_rate1")

    # For HV # Take candle size from the
    user_input_lookback_days_historical_volatility = parser.getint("USER INPUTS", "user_input_lookback_days_historical_volatility")
    user_input_average_historical_volatility_days = parser.getint("USER INPUTS", "user_input_average_historical_volatility_days")

    user_input_bar_size_historical_volatility = 1
    bar_size_historical_volatility = f"{user_input_bar_size_historical_volatility} hour"
    lookback_days_historical_volatility = f"{user_input_lookback_days_historical_volatility} D"
    duration_size_historical_volatility = (
        f"{user_input_average_historical_volatility_days  + user_input_lookback_days_historical_volatility - 1} D"
    )

    avg_iv_lookback_days = parser.getint("USER INPUTS", "avg_iv_lookback_days")

    # If the flag is False it will calcluate for all put-call strike otherwise for speicfic deltas
    flag_put_call_indicator_based_on_selected_deltas_only = parser.getboolean(
        "USER INPUTS", "flag_put_call_indicator_based_on_selected_deltas_only"
    )

    # Put Call Volume Variable
    user_input_lookback_days_for_pcr = parser.getint("USER INPUTS", "user_input_lookback_days_for_pcr")  # Days
    put_call_volume_lookback_days = f"{user_input_lookback_days_for_pcr} D"
    put_call_volume_bar_size_int = 4
    put_call_volume_bar_size = f"{put_call_volume_bar_size_int} hours"

    # get historical price data variables
    historical_price_data_bar_size_int = parser.getint("USER INPUTS", "historical_price_data_bar_size")
    historical_price_data_bar_size = f"{historical_price_data_bar_size_int} hours"

    list_of_percent_for_impact_calcluation_str = parser["USER INPUTS"][
        "list_of_percent_for_impact_calcluation"
    ]  # sorted(set([2, -2, 5, -5, 10, -10, 20, -20]))
    list_of_percent_for_impact_calcluation = [float(x.strip()) for x in list_of_percent_for_impact_calcluation_str.split(",")]
    list_of_percent_for_impact_calcluation = sorted(set(list_of_percent_for_impact_calcluation))

    ###########################
    # Scanner
    ###########################
    flag_force_restart_scanner = False
    rescan_time_in_seconds = parser.getfloat("USER INPUTS", "rescan_time_in_seconds")
    flag_recovery_mode = parser.getboolean("USER INPUTS", "flag_recovery_mode")

    # Indicator Cache time in seconds for the scanner
    indicator_cache_time_in_seconds = parser.getfloat("USER INPUTS", "indicator_cache_time_in_seconds")

    # Variables used in filtering in range 0 to 1 threshold
    flag_enable_filter_based_delta_threshold = parser.getboolean("USER INPUTS", "flag_enable_filter_based_delta_threshold")
    min_delta_threshold = 0.009
    max_delta_threshold = 0.990

    flag_store_csv_files = parser.getboolean("USER INPUTS", "flag_store_csv_files")
    o_c_s_folder_path = rf"{parser.get('USER INPUTS','o_c_s_folder_path')}"
    batch_size = 40
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

    columns_for_templates_to_csv = [
        "Leg No",
        "Instrument ID",
        "Action",
        "Right",
        "MinDelta",
        "MaxDelta",
        "MinDTE",
        "MaxDTE",

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

    lookback_input_for_change_in_avg_iv_since_yesterday = 1
    lookback_input_for_rr_change_since_yesterday = 1
    lookback_input_for_rr_change_over_n_days = 14
    hv_look_back_days = 14

    # Max min Pain Flag
    flag_drop_empty_oi_rows = True
    flag_test_print = False

    flag_ONE_for_max_pnl = "ONE"