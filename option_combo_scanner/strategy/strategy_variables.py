import configparser
import datetime
import threading
from typing import List, Tuple

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
    map_config_id_to_config_object = {}         # not using it anywhere, aryan created this but since there will be a single config in system, hence we are usign 'config_object'
    map_configleg_id_to_config_object = {}
    config_object = None

    nextorderId = None



    # Variables used in filtering in range 0 to 1 threshold
    flag_enable_filter_based_delta_threshold = True
    min_delta_threshold = 0.009
    max_delta_threshold = 0.990

    # Variable to map combo id to combination object
    map_combo_id_to_scanner_combination_object = {}

    screen = None

    scanner_combination_table_sort_by_column = {
        "Combo ID": False
    } 
        
    # Execution Engine Settings
    number_of_trades_allowed = int(execution_engine_config["number_of_trades_allowed"])
    max_ba_spread = float(execution_engine_config["max_ba_spread"])
    price_gap_threshold = float(execution_engine_config["price_gap_threshold"])
    stoploss_threshold = float(execution_engine_config["stoploss_threshold"])
    number_of_iterations = int(execution_engine_config["number_of_iterations"])
    sleep_time_between_iterations = float(
        execution_engine_config["sleep_time_between_iterations"]
    )

    trade_start_time = execution_engine_config["trade_start_time"]
    trade_end_time = execution_engine_config["trade_end_time"]

    max_nlv_exposure_per_trade = float(
        execution_engine_config["max_nlv_exposure_per_trade"]
    )

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