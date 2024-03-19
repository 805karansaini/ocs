"""
Created on 14-Mar-2023

@author: Karan
"""

from com.enum_input_class import *
import configparser

# Method to map candle size to candle size string
def get_candle_size(size_string):

    if 'ONE_MIN' in size_string:

        return CandleSize.ONE_MIN
    elif 'TWO_MIN' in size_string:

        return  CandleSize.TWO_MIN
    elif 'THREE_MIN' in size_string:

        return CandleSize.THREE_MIN
    elif 'FIVE_MIN' in size_string:

        return CandleSize.FIVE_MIN
    elif 'TEN_MIN' in size_string:

        return CandleSize.TEN_MIN
    elif 'FIFTEEN_MIN' in size_string:

        return CandleSize.FIFTEEN_MIN
    elif 'TWENTY_MIN' in size_string:

        return CandleSize.TWENTY_MIN
    elif 'THIRTY_MIN' in size_string:

        return CandleSize.THIRTY_MIN
    elif 'ONE_HOUR' in size_string:

        return CandleSize.ONE_HOUR
    elif 'TWO_HOUR' in size_string:

        return CandleSize.TWO_HOUR
    elif 'THREE_HOUR' in size_string:

        return CandleSize.THREE_HOUR

    else:
        return  CandleSize.FOUR_HOUR

# Map HV method to HV method string
def get_hv_method(method_str):

    if method_str == 'STANDARD_DEVIATION':

        return HVMethod.STANDARD_DEVIATION

    elif method_str == 'PARKINSON_WITH_GAP':

        return HVMethod.PARKINSON_WITH_GAP

    elif method_str == 'PARKINSON_WITHOUT_GAP':

        return  HVMethod.PARKINSON_WITHOUT_GAP

    else:

        return HVMethod.NATR

class UserInputs(object):


    parser = configparser.ConfigParser()
    parser.read('user_inputs.ini')



    # IBKR TWS params
    ibkr_tws_host = None #parser.get('USER INPUTS','ibkr_tws_host')  # Karan-Office PC "25.15.182.17"
    ibkr_tws_port = None #parser.getint('USER INPUTS','ibkr_tws_port')  # Value: Live A/C -> 7496, Paper A/C -> 7497
    ibkr_tws_connection_id = 12123
    ibkr_tws_connection_id_for_cas = 123531
    ibkr_account_number = "DU6484447"
    flag_recovery_mode = False
    flag_enable_hv_annualized = True
    flag_identification_print = False
    flag_simulate_prices = False
    flag_debug_mode = False
    flag_store_cas_tab_csv_files = True
    flag_cache_data = True
    flag_hv_daily = False
    flag_since_start_of_day_candles_for_relative_fields = True
    flag_enable_rm_account_rules = True
    flag_enable_trade_level_rm = True
    flag_use_execution_engine = False
    target_timezone = "Israel"
    account_parameter_for_order_quantity = "SMA"
    flag_series_condition = "AND"
    limit_price_selection_for_execution_engine = "Limit_Bid"
    offset_value_execution_engine = 0.23
    lookback_period_for_cache = 10
    time_frame_for_price_comparison_in_intraday = 60
    time_frame_for_price_range_ratio_in_intraday = 60
    ib_algo_priority = "Patient"
    max_wait_time_for_order_fill = 120


    # Number of days for which the values in CAS(Conditional Add or Switch) are computed # TODO - rename this
    cas_number_of_days = 20
    atr_number_of_days = 14
    relative_atr_in_range_number_of_buckets = 2
    flag_relative_atr_in_range = "Close In Range"


    # Historical Volatility Method
    hv_method = (
        get_hv_method("STANDARD_DEVIATION")
    )  # Methods available to calculate historic volatility(HV) is given as below
    # STANDARD_DEVIATION, PARKINSON_WITH_GAP, PARKINSON_WITHOUT_GAP, NATR

    # Duration size and Bar size values for Historical Volatility related data
    hv_look_back_days = 12
    hv_candle_size = get_candle_size('ONE_HOUR')
    #  ONE_MIN, TWO_MIN, THREE_MIN, FIVE_MIN, TEN_MIN , FIFTEEN_MIN, TWENTY_MIN, THIRTY_MIN
    #  ONE_HOUR, TWO_HOUR, THREE_HOUR, FOUR_HOUR,

    # Duration size and Bar size values for Volume related data
    volume_related_fileds_look_back_days = 10
    volume_related_fileds_candle_size = get_candle_size("THIRTY_MIN")
    #  ONE_MIN, TWO_MIN, THREE_MIN, FIVE_MIN, TEN_MIN , FIFTEEN_MIN, TWENTY_MIN, THIRTY_MIN
    #  ONE_HOUR, TWO_HOUR, THREE_HOUR, FOUR_HOUR,

    # lookback mins for relative vollume derivative
    relative_volume_derivation_lookback_mins = 15

    # lookback mins for relative atr derivative
    relative_atr_derivation_lookback_mins = 15

    # candle size for volume magnet
    volume_magnet_candle_size = get_candle_size("TWO_HOUR")

    # max lookback days fr volume magnet
    volume_magnet_max_lookback_days = 25

    # Duration Size and Bar size for support and resistance and all the relative values (rel atr, rel chg etc)
    support_resistance_and_relative_fields_look_back_days = 15
    support_resistance_and_relative_fields_candle_size = get_candle_size("THIRTY_MIN")
    #  ONE_MIN, TWO_MIN, THREE_MIN, FIVE_MIN, TEN_MIN , FIFTEEN_MIN, TWENTY_MIN, THIRTY_MIN
    #  ONE_HOUR, TWO_HOUR, THREE_HOUR, FOUR_HOUR,

    # Defining which index for which user want historical data
    index_select_for_beta_column = "SPY"  # Two choices - 'QQQ' or 'SPY'

    # candle size for rel volumn / rel chg (Must be multiple of last n minutes lookback
    last_n_minutes_fields_candle_size = get_candle_size("THIRTY_MIN")
    #  ONE_MIN, TWO_MIN, THREE_MIN, FIVE_MIN, TEN_MIN , FIFTEEN_MIN, TWENTY_MIN, THIRTY_MIN
    #  ONE_HOUR, TWO_HOUR, THREE_HOUR, FOUR_HOUR,

    # Lookback days for last n minutes fields
    last_n_minutes_fields_lookback_days = 10

    # lookback days for order parameter atr
    order_parameter_atr_lookback_days = 3

    # candle size for order parameter atr
    order_parameter_atr_candle_size = get_candle_size("THIRTY_MIN")
    #  ONE_MIN, TWO_MIN, THREE_MIN, FIVE_MIN, TEN_MIN , FIFTEEN_MIN, TWENTY_MIN, THIRTY_MIN
    #  ONE_HOUR, TWO_HOUR, THREE_HOUR, FOUR_HOUR,

    # range to calualte support adn resistance
    support_resistance_range_percent = 0.05
    cas_long_term_fields_update_interval = 600
    cas_intraday_fields_update_interval = 240
    hv_related_fields_update_interval_time = 300
    volume_related_fields_update_interval_time = 600
    support_resistance_and_relative_fields_update_interval_time = 600
    atr_for_order_interval = 300
    account_table_update_interval = 600
    rm_checks_interval_if_failed = 1
    trade_rm_check_update_interval = 600
    filter_conditions_update_interval = 200
    candle_for_order_interval = 500
    trade_level_rm_check_volume_lookback_mins = 30
    flag_rm_checks_trade_volume_and_or = "AND"
    volume_threshold_trade_rm_check = 1
    bid_ask_spread_threshold_trade_rm_check = 0.01
    bid_ask_qty_threshold_trade_rm_check = 1

    # candle size for order parameter candle
    order_parameter_candle_candle_size = get_candle_size("TWO_HOUR")
    #  ONE_MIN, TWO_MIN, THREE_MIN, FIVE_MIN, TEN_MIN , FIFTEEN_MIN, TWENTY_MIN, THIRTY_MIN
    #  ONE_HOUR, TWO_HOUR, THREE_HOUR, FOUR_HOUR,

    # flag for range orders
    flag_range_order = "Week"

    # flag for stop loss premium order
    flag_stop_loss_premium = "Positive Only"

    # flag for take profit premium order
    flag_take_profit_premium = "Both"

    # flag for trailing stop loss premium order
    flag_trailing_stop_loss_premium = "Both"

    # File path where CAS Table Values will be stored in CSV Format, so user can verify the accuracy of the values in CAS Table
    cas_tab_csv_file_path = "..\\ExecutionData"
    custom_columns_json_csv_file_path = "..\\CustomColumnJSON"
    buy_sell_csv = "..\\buy_sell_csv.csv"
    stk_currency = "USD"
    opt_currency = "USD"
    fut_currency = "USD"
    fop_currency = "USD"
    stk_exchange = "SMART"
    opt_exchange = "SMART"
    fut_exchange = "CME"
    fop_exchange = "CME"
    opt_lot_size = 100
    fut_lot_size = 50
    fop_lot_size = 50
        #########################################
    # The following params will not change
    #########################################

    # SQL params
    sql_host = "localhost"
    sql_user = "root"
    sql_password = ""

    # Active database
    active_sql_db_name = "option_combo_scanner_db"
    active_sql_connection_string = (
        "mysql+pymysql://" + sql_user + "@" + sql_host + "/" + active_sql_db_name
    )

    # Archive databse
    archive_sql_db_name = "archive_multileg_strat"
    archive_sql_connection_string = (
        "mysql+pymysql://" + sql_user + "@" + sql_host + "/" + archive_sql_db_name
    )

    # Tables name - Common for both database
    sql_table_combination = "combination"
    sql_table_combination_status = "combination_status"
    sql_table_order_status = "order_status"
    sql_table_cas_legs = "cas_legs"
    sql_table_cas_status = "cas_status"
    sql_table_cache = "cache_table"
    sql_table_meta_data = "meta_data"
    sql_table_watchlist = "watchlist"
    sql_table_ladder = "ladder_table"
    sql_table_sequence = "sequence_table"
    sql_table_account_group = "account_group"
    sql_table_account_conditions = "account_conditions"
    sql_table_filter_table = "filter_table"
    sql_table_conditional_series = "conditional_series_table"
    sql_table_conditional_series_sequence = "conditional_series_sequence_table"
    sql_table_series_cas_legs = "series_cas_legs"
    sql_table_series_positions = "series_positions"
