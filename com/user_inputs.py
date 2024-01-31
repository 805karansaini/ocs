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
    ibkr_tws_host = parser.get('USER INPUTS','ibkr_tws_host')  # Karan-Office PC "25.15.182.17"
    ibkr_tws_port = parser.getint('USER INPUTS','ibkr_tws_port')  # Value: Live A/C -> 7496, Paper A/C -> 7497
    ibkr_tws_connection_id = parser.getint('USER INPUTS','ibkr_tws_connection_id')
    ibkr_tws_connection_id_for_cas = parser.getint('USER INPUTS','ibkr_tws_connection_id_for_cas')

    # Account params
    # ibkr_account_number = "DU4214840"  # fgukp
    ibkr_account_number = parser.get('USER INPUTS','ibkr_account_number')  # gmma

    # Flags
    flag_recovery_mode = parser.getboolean('USER INPUTS','flag_recovery_mode')                                   # When set to 'True' Program will run in recovery mode.
    flag_enable_hv_annualized = parser.getboolean('USER INPUTS','flag_enable_hv_annualized')                            # When set to 'True' Historical Volatility will be Annualized else Non-Annualized
    flag_identification_print = parser.getboolean('USER INPUTS','flag_identification_print')                            # When Set to True Identification steps will be printed in console

    flag_simulate_prices = parser.getboolean('USER INPUTS','flag_simulate_prices')                                 # When set to "True" prices will be read from CSV file
    flag_debug_mode = parser.getboolean('USER INPUTS','flag_debug_mode')                                     # When set to 'True' extra detailed prints will printed in console (False is recommended)
    flag_store_cas_tab_csv_files = parser.getboolean('USER INPUTS','flag_store_cas_tab_csv_files')                         # When Set to 'True' for combination all the CSV(data files) using which the values are calculated will be stored.
    flag_cache_data = parser.getboolean('USER INPUTS','flag_cache_data')                                     # When Set to 'True' for NULL values in CAS table will be replaced by updated values in cache DB table
    flag_hv_daily = parser.getboolean('USER INPUTS','flag_hv_daily')                                       # When set to true hv will be calculated on daily candles
    flag_since_start_of_day_candles_for_relative_fields = parser.getboolean('USER INPUTS','flag_since_start_of_day_candles_for_relative_fields')  # When set to True it will consider candles since start of day for relative fields else it will consider only current candle
    flag_enable_rm_account_rules = parser.getboolean('USER INPUTS','flag_enable_rm_account_rules')                         # When flag set to True Account level RM checks will be performed

    flag_enable_trade_level_rm = parser.getboolean('USER INPUTS','flag_enable_trade_level_rm')                          # When flag set to True trade level RM checks will be performed
    flag_use_execution_engine = parser.getboolean('USER INPUTS','flag_use_execution_engine')                           # When true, execution engine will be used for order placement

    # TimeZone
    target_timezone = parser.get('USER INPUTS','target_timezone')  # Israel

    # Account parameter selected
    account_parameter_for_order_quantity = parser.get('USER INPUTS','account_parameter_for_order_quantity')  # NLV, SMA, CEL

    # flag value for series id condition
    flag_series_condition = parser.get('USER INPUTS','flag_series_condition')  # AND, OR



    # Limit price for execution engine
    limit_price_selection_for_execution_engine = parser.get('USER INPUTS','limit_price_selection_for_execution_engine')
        # Limit_Bid, Limit_Ask, Limit_Mid, Pegged_Market, Pegged_Midpoint


    # offset value for pegged type order
    offset_value_execution_engine = parser.getfloat('USER INPUTS','offset_value_execution_engine')

    # Cache LookBack in Minutes
    lookback_period_for_cache = parser.getint('USER INPUTS','lookback_period_for_cache')  # Time lookback upto which the cache data will be used in the execution system

    # Lookback period to compare prices occured in a day which will be divided in to 2 time frames in terms of candle number
    time_frame_for_price_comparison_in_intraday = parser.getint('USER INPUTS','time_frame_for_price_comparison_in_intraday')  # Value is for number of minutes

    # Lookback period to compare price range occured in a past time frame to price range occured in a whole day
    time_frame_for_price_range_ratio_in_intraday = parser.getint('USER INPUTS','time_frame_for_price_range_ratio_in_intraday')  # Value is for number of minutes

    # IB Algo Order Priority
    ib_algo_priority = parser.get('USER INPUTS','ib_algo_priority')  # Urgent > Normal > Patient, read More: https://interactivebrokers.github.io/tws-api/ibalgos.html
    max_wait_time_for_order_fill = parser.getint('USER INPUTS','max_wait_time_for_order_fill')  # Maximum time before locks are released on the ticker, so new orders can be sent for the same ticker

    # Number of days for which the values in CAS(Conditional Add or Switch) are computed # TODO - rename this
    cas_number_of_days = parser.getint('USER INPUTS','cas_number_of_days')  # Look back

    # Number of days for which the values of Combination ATR will be computed
    atr_number_of_days = parser.getint('USER INPUTS','atr_number_of_days')  # Lock back for ATR

    # number of buckets for relative atr in range
    relative_atr_in_range_number_of_buckets = parser.getint('USER INPUTS','relative_atr_in_range_number_of_buckets')

    # flag for realtive atr in range
    flag_relative_atr_in_range = (
        parser.get('USER INPUTS','flag_relative_atr_in_range')  # Open In Range, Close In Range, Open Or Close In Range
    )

    # Historical Volatility Method
    hv_method = (
        get_hv_method(parser.get('USER INPUTS','hv_method'))
    )  # Methods available to calculate historic volatility(HV) is given as below
    # STANDARD_DEVIATION, PARKINSON_WITH_GAP, PARKINSON_WITHOUT_GAP, NATR

    # Duration size and Bar size values for Historical Volatility related data
    hv_look_back_days = parser.getint('USER INPUTS','hv_look_back_days')  #  Number of trading days
    hv_candle_size = get_candle_size(parser.get('USER INPUTS','hv_candle_size'))
    #  ONE_MIN, TWO_MIN, THREE_MIN, FIVE_MIN, TEN_MIN , FIFTEEN_MIN, TWENTY_MIN, THIRTY_MIN
    #  ONE_HOUR, TWO_HOUR, THREE_HOUR, FOUR_HOUR,

    # Duration size and Bar size values for Volume related data
    volume_related_fileds_look_back_days = parser.getint('USER INPUTS','volume_related_fileds_look_back_days')
    volume_related_fileds_candle_size = get_candle_size(parser.get('USER INPUTS','volume_related_fileds_candle_size'))
    #  ONE_MIN, TWO_MIN, THREE_MIN, FIVE_MIN, TEN_MIN , FIFTEEN_MIN, TWENTY_MIN, THIRTY_MIN
    #  ONE_HOUR, TWO_HOUR, THREE_HOUR, FOUR_HOUR,

    # lookback mins for relative vollume derivative
    relative_volume_derivation_lookback_mins = parser.getint('USER INPUTS','relative_volume_derivation_lookback_mins')  # In minutes

    # lookback mins for relative atr derivative
    relative_atr_derivation_lookback_mins = parser.getint('USER INPUTS','relative_atr_derivation_lookback_mins')  # In minutes

    # candle size for volume magnet
    volume_magnet_candle_size = get_candle_size(parser.get('USER INPUTS','volume_magnet_candle_size'))

    # max lookback days fr volume magnet
    volume_magnet_max_lookback_days = parser.getint('USER INPUTS','volume_magnet_max_lookback_days')  # in days

    # Duration Size and Bar size for support and resistance and all the relative values (rel atr, rel chg etc)
    support_resistance_and_relative_fields_look_back_days = parser.getint('USER INPUTS','support_resistance_and_relative_fields_look_back_days')
    support_resistance_and_relative_fields_candle_size = get_candle_size(parser.get('USER INPUTS','support_resistance_and_relative_fields_candle_size'))
    #  ONE_MIN, TWO_MIN, THREE_MIN, FIVE_MIN, TEN_MIN , FIFTEEN_MIN, TWENTY_MIN, THIRTY_MIN
    #  ONE_HOUR, TWO_HOUR, THREE_HOUR, FOUR_HOUR,

    # Defining which index for which user want historical data
    index_select_for_beta_column = parser.get('USER INPUTS','index_select_for_beta_column')  # Two choices - 'QQQ' or 'SPY'

    # candle size for rel volumn / rel chg (Must be multiple of last n minutes lookback
    last_n_minutes_fields_candle_size = get_candle_size(parser.get('USER INPUTS','last_n_minutes_fields_candle_size'))
    #  ONE_MIN, TWO_MIN, THREE_MIN, FIVE_MIN, TEN_MIN , FIFTEEN_MIN, TWENTY_MIN, THIRTY_MIN
    #  ONE_HOUR, TWO_HOUR, THREE_HOUR, FOUR_HOUR,

    # Lookback days for last n minutes fields
    last_n_minutes_fields_lookback_days = parser.getint('USER INPUTS','last_n_minutes_fields_lookback_days')  # In days

    # lookback days for order parameter atr
    order_parameter_atr_lookback_days = parser.getint('USER INPUTS','order_parameter_atr_lookback_days')

    # candle size for order parameter atr
    order_parameter_atr_candle_size = get_candle_size(parser.get('USER INPUTS','order_parameter_atr_candle_size'))
    #  ONE_MIN, TWO_MIN, THREE_MIN, FIVE_MIN, TEN_MIN , FIFTEEN_MIN, TWENTY_MIN, THIRTY_MIN
    #  ONE_HOUR, TWO_HOUR, THREE_HOUR, FOUR_HOUR,

    # range to calualte support adn resistance
    support_resistance_range_percent = parser.getfloat('USER INPUTS','support_resistance_range_percent') / 100

    # Time interval after which the CAS(Conditional Add or Switch) values will be updated
    cas_long_term_fields_update_interval = parser.getint('USER INPUTS','cas_long_term_fields_update_interval')  # Seconds
    cas_intraday_fields_update_interval = parser.getint('USER INPUTS','cas_intraday_fields_update_interval')  # Seconds
    hv_related_fields_update_interval_time = parser.getint('USER INPUTS','hv_related_fields_update_interval_time')  # Seconds
    volume_related_fields_update_interval_time = parser.getint('USER INPUTS','volume_related_fields_update_interval_time')  # Seconds
    support_resistance_and_relative_fields_update_interval_time = parser.getint('USER INPUTS','support_resistance_and_relative_fields_update_interval_time')  # Seconds
    atr_for_order_interval = parser.getint('USER INPUTS','atr_for_order_interval')  # seconds
    account_table_update_interval = parser.getint('USER INPUTS','account_table_update_interval')  # seconds
    rm_checks_interval_if_failed = parser.getint('USER INPUTS','rm_checks_interval_if_failed')  # Seconds
    trade_rm_check_update_interval = parser.getint('USER INPUTS','trade_rm_check_update_interval')  # seconds
    filter_conditions_update_interval = parser.getint('USER INPUTS','filter_conditions_update_interval')  # seconds
    candle_for_order_interval = parser.getint('USER INPUTS','candle_for_order_interval') # seconds

    # trade rm check volume lookback minutes
    trade_level_rm_check_volume_lookback_mins = parser.getint('USER INPUTS','trade_level_rm_check_volume_lookback_mins')

    flag_rm_checks_trade_volume_and_or = parser.get('USER INPUTS','flag_rm_checks_trade_volume_and_or')  # Possible two values 'AND' or 'OR'

    # threshold for volume trade level RM check
    volume_threshold_trade_rm_check = parser.getfloat('USER INPUTS','volume_threshold_trade_rm_check')

    # threshold for bid ask spread trade level RM check
    bid_ask_spread_threshold_trade_rm_check = parser.getfloat('USER INPUTS','bid_ask_spread_threshold_trade_rm_check') / 100.0

    # threshold for bid ask qty trade level RM check
    bid_ask_qty_threshold_trade_rm_check = parser.getfloat('USER INPUTS','bid_ask_qty_threshold_trade_rm_check')

    # candle size for order parameter candle
    order_parameter_candle_candle_size = get_candle_size(parser.get('USER INPUTS','order_parameter_candle_candle_size'))
    #  ONE_MIN, TWO_MIN, THREE_MIN, FIVE_MIN, TEN_MIN , FIFTEEN_MIN, TWENTY_MIN, THIRTY_MIN
    #  ONE_HOUR, TWO_HOUR, THREE_HOUR, FOUR_HOUR,

    # flag for range orders
    flag_range_order = parser.get('USER INPUTS','flag_range_order') #Intraday, Week, Month

    # flag for stop loss premium order
    flag_stop_loss_premium = parser.get('USER INPUTS','flag_stop_loss_premium')  # Positive Only, Negative Only, Both

    # flag for take profit premium order
    flag_take_profit_premium = parser.get('USER INPUTS','flag_take_profit_premium')  # Positive Only, Negative Only, Both

    # flag for trailing stop loss premium order
    flag_trailing_stop_loss_premium = parser.get('USER INPUTS','flag_trailing_stop_loss_premium')  # Positive Only, Negative Only, Both

    # File path where CAS Table Values will be stored in CSV Format, so user can verify the accuracy of the values in CAS Table
    cas_tab_csv_file_path = parser.get('USER INPUTS','cas_tab_csv_file_path')  # Folder path

    # File path for custom columns json file
    custom_columns_json_csv_file_path = parser.get('USER INPUTS','custom_columns_json_csv_file_path')  # Folder path

    # File path CSV File from where user can manupulate the price of combination
    buy_sell_csv = parser.get('USER INPUTS','buy_sell_csv')  # Exact File Path

    # Default Values
    # Combo Creator Defaults value
    stk_currency = parser.get('USER INPUTS','stk_currency')
    opt_currency = parser.get('USER INPUTS','opt_currency')
    fut_currency = parser.get('USER INPUTS','fut_currency')
    fop_currency = parser.get('USER INPUTS','fop_currency')
    stk_exchange = parser.get('USER INPUTS','stk_exchange')
    opt_exchange = parser.get('USER INPUTS','opt_exchange')
    fut_exchange = parser.get('USER INPUTS','fut_exchange')
    fop_exchange = parser.get('USER INPUTS','fop_exchange')

    # Default Lot size
    opt_lot_size = parser.getint('USER INPUTS','opt_lot_size')
    fut_lot_size = parser.getint('USER INPUTS','fut_lot_size')
    fop_lot_size = parser.getint('USER INPUTS','fop_lot_size')
    # For STKs the Multiplier must be '1' by default always

    #########################################
    # The following params will not change
    #########################################

    # SQL params
    sql_host = "localhost"
    sql_user = "root"
    sql_password = ""

    # Active database
    active_sql_db_name = "multileg_strat"
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
