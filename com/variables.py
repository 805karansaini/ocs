"""
Created on 14-Mar-2023

@author: Karan
"""

from com import *
from com.user_inputs import *


class variables(object):

    # TWS API Params
    ibkr_tws_host = UserInputs.ibkr_tws_host
    ibkr_tws_port = UserInputs.ibkr_tws_port
    ibkr_tws_connection_id = UserInputs.ibkr_tws_connection_id
    ibkr_tws_connection_id_for_cas = UserInputs.ibkr_tws_connection_id_for_cas

    # Flags
    flag_debug_mode = UserInputs.flag_debug_mode
    flag_enable_hv_annualized = UserInputs.flag_enable_hv_annualized
    flag_recovery_mode = UserInputs.flag_recovery_mode
    flag_store_cas_tab_csv_files = UserInputs.flag_store_cas_tab_csv_files
    flag_market_open = False
    flag_use_rth = 1  # Historical data
    flag_cancel_subscription = True  # Currently not being used anywhere, this is typically used when we make a call to reqMktData
    flag_snapshot_req_mkt_data = (
        True  # Use snapshot data for reqMktData calls for combos
    )
    flag_use_rth_und_data = False  # Use RTH only for real time bars for the underlying
    flag_audio_alert = False
    flag_identification_print = UserInputs.flag_identification_print
    flag_simulate_prices = UserInputs.flag_simulate_prices
    # flag_weighted_change_in_price = UserInputs.flag_weighted_change_in_price
    flag_weighted_change_in_price = True  # When Set to 'True' for change from open and change form close will be calculated using weighted average

    flag_cache_data = (
        UserInputs.flag_cache_data
    )  # Flag to check if user wants cache data feature to use or not
    flag_hv_daily = (
        UserInputs.flag_hv_daily
    )  # When set to true hv will be calculated on daily candles
    flag_since_start_of_day_candles_for_relative_fields = (
        UserInputs.flag_since_start_of_day_candles_for_relative_fields
    )  # When set to True it will consider candles since start of day for relative fields else it will consider only current candle
    flag_enable_rm_account_rules = (
        UserInputs.flag_enable_rm_account_rules
    )  # When flag set to True RM checks will be performed
    flag_account_checks_completed_first_time = False
    flag_account_checks_completed_wait = False
    flag_rm_checks_trade_volume_and_or = UserInputs.flag_rm_checks_trade_volume_and_or
    flag_enable_trade_level_rm = UserInputs.flag_enable_trade_level_rm
    flag_enable_filter_condition = False
    flag_use_execution_engine = UserInputs.flag_use_execution_engine

    # flag value for series id condition
    flag_series_condition = UserInputs.flag_series_condition

    # flag for stop loss premium order
    flag_stop_loss_premium = UserInputs.flag_stop_loss_premium

    # flag for take profit premium order
    flag_take_profit_premium = UserInputs.flag_take_profit_premium

    # flag for trailing stop loss premium order
    flag_trailing_stop_loss_premium = UserInputs.flag_trailing_stop_loss_premium

    # Dict for checking if requested data has ended
    flag_account_update_ended = {}

    # Dict for flag of liquidation mode
    flag_account_liquidation_mode = {}

    # Dict for flag of trade level em checks
    flag_trade_level_rm_checks = {}

    # flag for calling pnl single
    flag_pnl_single = False

    # list to store req ids for pnl
    pnl_single_req_ids = []

    
    # Time Zone
    target_timezone = "Israel"

    target_timezone_obj = pytz.timezone(target_timezone)

    # Standarrd Currency
    standard_currency_for_account_value = "USD"

    # Account parameter selected
    account_parameter_for_order_quantity = (
        UserInputs.account_parameter_for_order_quantity
    )  # NLV, SMA, CEL

    # execution engine limit price
    limit_price_selection_for_execution_engine = (
        UserInputs.limit_price_selection_for_execution_engine
    )

    # offset value for pegged type order
    offset_value_execution_engine = UserInputs.offset_value_execution_engine

    # Internal variables init
    nextorderId = None
    sleep_time_waiting_for_tws_response = 0.1  # Used when waiting for response from TWS
    sleep_time_db = 0.2
    sleep_time_ibkr_orders = 2
    sleep_time_between_iters = 1
    sleep_time_ten_seconds = (
        10  # Used in recovery mode, After getting order execution details
    )
    max_wait_time_for_mkt_data = 14
    sleep_time_wait_bid_ask_legs = 10

    # When creating Price Chart, max-time we will wait
    wait_time_for_historical_data = 60

    # Wait time for historical data when we are fethcing values for CAS Tab
    cas_wait_time_for_historical_data = 600

    # When User auto updates the PriceChart..  if chart window is closed. End Thread (quicker) using this time.
    sleep_iteration_price_chart = 1

    # List of Trading accounts
    current_session_accounts = []

    # Dict to map req id to account id
    map_req_id_to_account_id = {}

    # Max Available unique id ( for combos, in main module it is update at the start)
    unique_id = 0

    # Max Available ladder id ( for scale trade, in main module it is update at the start)
    ladder_id = 0

    # Max Available sequence id ( for scale trade, in main module it is update at the start)
    sequence_id = 0

    # Max avaialble custom column id( for custom columns, in main module it is update at the start)
    custom_column_id = 0

    # Lookback period to compare prices occured in a day which will be divided in to 2 time frames in terms of candle number
    time_frame_for_price_comparison_in_intraday = (
        UserInputs.time_frame_for_price_comparison_in_intraday
    )  # Value is for number of candles

    # Lookback period to compare price range occured in a past time frame to price range occured in a whole day
    time_frame_for_price_range_ratio_in_intraday = (
        UserInputs.time_frame_for_price_range_ratio_in_intraday
    )  # Value is for number of minutes

    expiry_dates = {}
    strike_prices = {}
    contract_details = {}
    contract_details_end = {}
    options_delta_bid = {}
    options_delta_ask = {}
    options_delta = {}
    options_iv_bid = {}
    options_iv_ask = {}
    options_iv_last = {}
    call_option_open_interest = {}
    put_option_open_interest = {}
    options_vega = {}
    options_theta = {}
    options_gamma = {}

    live_und_price = None

    # dict for storing price candle data
    bid_price = {}
    ask_price = {}
    bid_size = {}
    ask_size = {}
    volume = {}
    high_price = {}
    low_price = {}
    close_price = {}
    price_data_update_time = {}

    req_error = {}  # dict used to check if error received for the request

    contract_details = (
        {}
    )  # Contract details will be stored here using reqId as a dictionary key
    req_mkt_data_end = {}  # dict to store whether reqMktData response has ended
    contract_details_end = (
        {}
    )  # dict to store whether reqContractDetails response has ended

    req_sec_def_end = (
        {}
    )  # dict to store whether SecurityDefinitionOptionParameter response has ended

    bool_account_value_available = (
        False  # Do We have Account Value Available? (NetLiquidationByCurrency)
    )
    bool_account_summary_end = False  # Has the account summary response ended
    account_value = None  # Account Value Net Liquidation

    recovery_mode_input_tk = False

    # Get ExecutionDetails
    execution_details = {}
    string_exec = []

    # Flag storing Execution End Detail
    bool_execution_details = False

    #########################################################################
    #    VERSION 1
    #########################################################################

    # dict stores live price of underlying/ticker {req_id : price}
    live_price_ticker = {}

    # Account
    ibkr_account_number = UserInputs.ibkr_account_number

    order_type = "MKT"  # For Order Placement,
    multileg_bid_ask = {}

    # Index for Beta Calculation. Two choices - 'QQQ' or 'SPY'
    index_select_for_beta_column = UserInputs.index_select_for_beta_column

    # Print Lock()
    print_lock = Semaphore(1)

    ########################################
    # SQL
    ########################################

    # Sql
    sql_host = UserInputs.sql_host
    sql_user = UserInputs.sql_user
    sql_password = UserInputs.sql_password

    # Active database
    active_sql_db_name = UserInputs.active_sql_db_name
    active_sql_connection_string = UserInputs.active_sql_connection_string

    # Establish Database connection
    active_sqlalchemy_connection = sqlalchemy.create_engine(
        active_sql_connection_string
    )
    active_pymysql_connection = pymysql.connect(
        host=sql_host, user=sql_user, password=sql_password, db=active_sql_db_name
    )

    # Archive databse
    archive_sql_db_name = UserInputs.archive_sql_db_name
    archive_sql_connection_string = UserInputs.archive_sql_connection_string

    # Establish Database connection
    archive_sqlalchemy_connection = sqlalchemy.create_engine(
        archive_sql_connection_string
    )
    # archive_pymysql_connection = pymysql.connect(
    #     host=sql_host, user=sql_user, password=sql_password, db=archive_sql_db_name
    # )

    cursor = None

    # Tables in Databases - common for both
    sql_table_combination = UserInputs.sql_table_combination
    sql_table_combination_status = UserInputs.sql_table_combination_status
    sql_table_order_status = UserInputs.sql_table_order_status
    sql_table_meta_data = UserInputs.sql_table_meta_data
    sql_table_cache = UserInputs.sql_table_cache
    sql_table_cas_legs = UserInputs.sql_table_cas_legs
    sql_table_cas_status = UserInputs.sql_table_cas_status
    sql_table_watchlist = UserInputs.sql_table_watchlist
    sql_table_ladder = UserInputs.sql_table_ladder
    sql_table_sequence = UserInputs.sql_table_sequence
    sql_table_account_group = UserInputs.sql_table_account_group
    sql_table_account_conditions = UserInputs.sql_table_account_conditions
    sql_table_filter_table = UserInputs.sql_table_filter_table
    sql_table_conditional_series = UserInputs.sql_table_conditional_series
    sql_table_conditional_series_sequence = (
        UserInputs.sql_table_conditional_series_sequence
    )
    sql_table_series_cas_legs = UserInputs.sql_table_series_cas_legs
    sql_table_series_positions = UserInputs.sql_table_series_positions

    # NOTE: NOT ADDING THE METADATA and WATCHLIST TABLE AS THE AUTOMATION IS STRUCTURES WHEN A COMBO IS DELETED, ALL THE INFO FROM ACTIVE DB WILL BE MOVED TO ARCHVE DB.
    # below are all the tables from where the data will be moved
    # List of all the tables in the DB
    all_sql_tables_in_db = [
        sql_table_combination,
        sql_table_combination_status,
        sql_table_order_status,
        sql_table_cache,
        # sql_table_cas_legs,
        sql_table_cas_status,
        # sql_table_account_conditions,
        # sql_table_conditional_series,
        # sql_table_conditional_series_sequence,
        # sql_table_series_cas_legs,
        # sql_table_series_positions,
        sql_table_ladder,
        sql_table_sequence,
    ]  # contains all the sql_tables_name in our DB

    all_sql_tables_in_db_with_correct_dropping_order = [
        sql_table_combination,
        sql_table_combination_status,
        sql_table_order_status,
        sql_table_cache,
        sql_table_cas_legs,
        sql_table_cas_status,
        # sql_table_account_conditions,
        sql_table_conditional_series,
        sql_table_conditional_series_sequence,
        sql_table_series_cas_legs,
        sql_table_series_positions,
        sql_table_sequence,
        sql_table_ladder,
    ]

    # List of all the DB
    all_sql_databases = [active_sql_db_name, archive_sql_db_name]

    ##########
    lut_for_long_term_values = None
    lut_for_intraday_values = None
    lut_for_hv_related_columns = None
    lut_for_volume_related_fields = None
    lut_for_price_based_relative_indicators_values = None

    time_buffer_for_keep_updating_lut_time_for_fetched_values = 2  # Minute

    ##########
    conid_mktdata_subscription_dict = {}
    con_id_to_req_id_dict = {}
    unique_id_to_combo_obj = {}
    unique_id_to_prices_dict = {}
    unique_id_to_actual_prices_dict = {}

    # TODO - ashish done
    columns_for_leg_to_combo_comparision = (
        "Action",
        "Symbol",
        "#Lots",
        "Multiplier",
        "HV Leg-to-Combo",
        "High Price Leg-to-Combo",
        "Change in Price Leg-to-Combo",
    )

    columns_for_download_combo_to_csv = [
        "Type",
        "Action",
        "SecType",
        "Symbol",
        "DTE",
        "Delta",
        "Right",
        "#Lots",
        "Multiplier",
        "Exchange",
        "Trading Class",
        "Currency",
        "ConID",
        "Primary Exchange",
        "Strike",
        "Expiry",
    ]

    columns_for_download_orders_to_csv = [
        "Unique ID",
        "Action",
        "Order Type",
        "#Lots",
        "Limit Price",
        "Trigger Price",
        "Trail Value",
        "ATR Multiple",
        "Account ID",
        "Bypass RM Check",
    ]

    # TODO
    # Selected watchlist name
    selected_watchlist = "ALL"
    # Unique Id list for Selected watchlist
    unique_id_list_of_selected_watchlist = "ALL"

    unique_ids_list_of_passed_condition = []

    # Selected account group name
    selected_account_group = "ALL"

    # Account ids in slected account group
    account_ids_list_of_selected_acount_group = "ALL"

    flag_update_tables_watchlist_changed = False
    flag_update_combo_tables_watchlist_changed = False
    flag_market_watch_tables_watchlist_changed = False
    flag_positions_tables_watchlist_changed = False
    flag_orders_book_table_watchlist_changed = False
    flag_cas_condition_table_watchlist_changed = False
    flag_scale_trade_tables_watchlist_changed = False

    # Combo table columns
    combo_table_columns = (
        "Unique ID",
        "#Legs",
        "Tickers",
        "#Buys",
        "#Sells",
        "#STK",
        "#FUT",
        "#OPT",
        "#FOP",
    )

    market_watch_table_columns = (
        "Unique ID",
        "#Legs",
        "Tickers",
        "Sell Price",
        "Buy Price",
        "Bid - Ask Spread",
    )

    positions_table_columns = (
        "Unique ID",
        "#Legs",
        "Tickers",
        "#Net Position",
        "Account ID",
        "Account ID Unique ID Combo",
    )

    order_book_table_columns = (
        "Unique ID",
        "Account ID",
        "Tickers",
        "Action",
        "#Lots",
        "Order Type",
        "Order Time",
        "Last Update Time",
        "Entry Price",
        "Limit Price",
        "Trigger Price",
        "Reference Price",
        "Trail Value",
        "Status",
        "Reason For Failed",
        "Ladder ID",
        "Sequence ID",
        "ATR Multiple",
        "ATR",
        "Bypass RM Check",
        "Execution Engine",
        "Limit IV",
        "Trigger IV",
        'Actual Entry Price'
    )

    order_book_table_df_columns = (
        "Unique ID",
        "Account ID",
        "Tickers",
        "Action",
        "#Lots",
        "Order Type",
        "Order Time",
        "Last Update Time",
        "Entry Price",
        "Limit Price",
        "Trigger Price",
        "Reference Price",
        "Trail Value",
        "Status",
        "Reason For Failed",
        "Ladder ID",
        "Sequence ID",
        "ATR Multiple",
        "ATR",
        "Bypass RM Check",
        "Execution Engine",
        "Limit IV",
        "Trigger IV",
        'Actual Entry Price'
    )

    cas_condition_table_columns = [
        "Unique ID",
        "Trading Combo Unique ID",
        "Evaluation Unique ID",
        "Add/Switch",
        "Incremental Tickers",
        "Condition",
        "Reference Price",
        "Reference Position",
        "Target Position",
        "Trigger Price",
        "Status",
        "Reason For Failed",
        "Correlation",
        "Account ID",
        "Execution Engine",
        "Series ID",
        "Table ID Column",
    ]

    # Scale Trader columns
    scale_trader_table_columns_name_heading = [
        ("Ladder ID", "Ladder ID"),
        ("Unique ID", "Unique ID"),
        ("Action", "Action"),
        ("Order Type", "Order Type"),
        ("Total Quantity", "Total Quantity"),
        ("Initial Quantity", "   Initial\nQuantity"),
        ("Subsequent Quantity", "Subsequent\n   Quantity"),
        ("Number of Buckets", "Number of\n   Buckets"),
        ("Initial Entry Price", "Initial Entry Price"),
        ("Delta Price", "Delta Price"),
        ("Price Movement", "Price Movement"),
        ("Take Profit Buffer", "Take Profit Buffer"),
        ("Take Profit Behaviour", "Take Profit\n Behaviour"),
        ("Entry Quantity Filled", "Entry Quantity\n        Filled"),
        ("Exit Quantity Filled", "Exit Quantity\n       Filled"),
        ("Status", "Status"),
        ("Account ID", "Account ID"),
        ("Bypass RM Check", "Bypass RM\nCheck"),
        ("Execution Engine", "Execution\nEngine"),
    ]

    # Column names for scale trader table
    scale_trader_table_columns = [
        col_name for col_name, x in scale_trader_table_columns_name_heading
    ]

    # Sequence table columns
    sequence_table_columns = [
        "Sequence ID",
        "Sequence Type",
        "Ladder ID",
        "Action",
        "Order Type",
        "Quantity",
        "Price",
        "Order Time",
        "Order Sent Time",
        "Last Update time",
        "Filled Quantity",
        "Status",
        "Percentage"
    ]

    # Custom columns table columns
    custom_columns_table_columns = [
        "Column ID",
        "Column Name",
        " Column Expression",
        "Column Description",
    ]

    # Account group table column
    accounts_group_table_columns = ["Group ID", "Group Name", "Account IDs"]

    # Account table columns
    accounts_table_columns = [
        "Account ID",
        "Net Liquidity Value",
        "Special Memorandum Account",
        "Day Profit and Loss",
        "Current Excess Liquidity",
        "Utilised Margin",
        "Liquidation Mode",
    ]

    # account condition table
    account_conditions_table_columns = ["Account ID", "Condition", "Table ID"]

    # filter table columns
    filter_table_columns = ["Condition Name", "Condition", "Active"]

    # portfolio table columns
    portfolio_table_combo_columns = ['Unique ID', '#Legs', 'Tickers', '#Net Position', 'Realized PNL', 'Unrealized PNL', 'Account ID', 'Entry Price']

    # portfolio table columns
    portfolio_table_legs_columns = ['Leg Description', '#Net Position', 'Account ID',  'Realized PNL', 'Unrealized PNL', 'Entry Price'
                                     ]


    # conditional series table columns
    conditional_series_table_columns = [
        "Series ID",
        "Unique ID",
        "Account ID",
        "Total Sequences",
        "Sequences Completed",
        "Status",
        "Bypass RM Check",
        "Execution Engine",
        "Evaluation Unique ID",
        "Combination Condition",
        "Series ID Condition",
        "Is Started Once",
        "Multi Account",
        "Reference Price",
        "Reference Position",
    ]

    # conditional series orders table columns
    conditional_series_sequence_table_columns = [
        "Sequence ID",
        "Series ID",
        "Unique ID",
        "Trading Unique ID",
        "Evaluation Unique ID",
        "Add/Switch/Buy/Sell",
        "Incremental Tickers",
        "Condition",
        "Reference Position",
        "Target Position",
        "Status",
        "Order Type",
        "#Lots",
        "Limit Price",
        "Trigger Price",
        "Trail Value",
        "ATR Multiple",
    ]

    # series sequnece gui table columns

    series_sequence_tble_columns = [
        "Unique ID",
        "Trading Unique ID",
        "Evaluation Unique ID",
        "Add/Switch/Buy/Sell",
        "Incremental Tickers",
        "Condition",
        "Status",
        "Order Type",
        "#Lots",
        "Limit Price",
        "Trigger Price",
        "Trail Value",
        "ATR Multiple",
        "Table ID",
        "Combo Obj",
        "Reference Position",
        "Target Position",
    ]
    # Combination table dataframe
    combo_table_df = pd.DataFrame(columns=combo_table_columns)

    # Market Wacth Table Dataframe consist of all the row of the table.
    market_watch_table_dataframe = pd.DataFrame(columns=market_watch_table_columns)

    # Positions Table Dataframe consist of all the row of the table.
    positions_table_dataframe = pd.DataFrame(columns=positions_table_columns)

    # Positions Table Dataframe consist of all the row of the table.
    orders_book_table_dataframe = pd.DataFrame(columns=order_book_table_df_columns)

    # cas condition Table Dataframe consist of all the row of the table.
    cas_condition_table_dataframe = pd.DataFrame(columns=cas_condition_table_columns)

    # Scale Trader table dataframe consisting all rows in table
    scale_trade_table_dataframe = pd.DataFrame(columns=scale_trader_table_columns)

    # custom column table dataframe consisting all rows in json file
    custom_columns_table_dataframe = pd.DataFrame(columns=custom_columns_table_columns)

    # Accounts tble dataframe
    accounts_table_dataframe = pd.DataFrame(columns=accounts_table_columns)

    # Accounts conditions dataframe
    accounts_conditions_table_dataframe = pd.DataFrame(
        columns=account_conditions_table_columns
    )

    # create series sequence table df
    series_sequence_table_df = []

    ## Default maps ##
    currency = "USD"
    default_sec_type_to_exchange = {
        "STK": UserInputs.stk_exchange,
        "FUT": UserInputs.fut_exchange,
        "OPT": UserInputs.opt_exchange,
        "FOP": UserInputs.fop_exchange,
    }

    stk_lot_size = 1
    defaults = {
        "STK": [
            UserInputs.stk_currency,
            UserInputs.stk_exchange,
            stk_lot_size,
        ],
        "OPT": [
            UserInputs.opt_currency,
            UserInputs.opt_exchange,
            UserInputs.opt_lot_size,
        ],
        "FUT": [
            UserInputs.fut_currency,
            UserInputs.fut_exchange,
            UserInputs.fut_lot_size,
        ],
        "FOP": [
            UserInputs.fop_currency,
            UserInputs.fop_exchange,
            UserInputs.fop_lot_size,
        ],
    }

    # TESTING
    buy_sell_csv = UserInputs.buy_sell_csv

    ########################################
    # Identified Butterfly
    ########################################
    INF = 10**10
    bfly_buy_levels = {}
    bfly_sell_levels = {}
    bfly_order_qty = {}
    blfy_ba_spread = {}
    bfly_balancing_ratio = {}

    # Used in dataframe to show nearest expiry
    df_expiry_summary_header_col1 = "Expiry Date"
    df_expiry_summary_header_col2 = "Target Date Diff"
    df_expiry_summary_header_col3 = "Expiry DTE"

    # Used in get the nearest Strike such that the delta difference is minumum
    df_strike_summary_header_col1 = "Strike Price"
    df_strike_summary_header_col2 = "Strike Delta"
    df_strike_summary_header_col3 = "Target Delta Diff"

    # Used in search_strike_bidask_spread such that the spread difference is minumum
    df_bid_ask_search_summary_header_col1 = "Strike Price"
    df_bid_ask_search_summary_header_col2 = "Bid Price"
    df_bid_ask_search_summary_header_col3 = "Ask Price"
    df_bid_ask_search_summary_header_col4 = "Bid-Ask Spread"

    # Used in print_butterfly to print the butterfly in tabular form
    df_butterfly_summary_header_col1 = "Leg No."
    df_butterfly_summary_header_col2 = "Ticker"
    df_butterfly_summary_header_col3 = "Exchange"
    df_butterfly_summary_header_col4 = "Expiry Date"
    df_butterfly_summary_header_col5 = "Right"
    df_butterfly_summary_header_col6 = "Strike Price"
    df_butterfly_summary_header_col7 = "ConId"

    ######## Order LOCKING #####################

    # lock for tickers
    order_lock = {}

    # Lock on order sending
    order_sending_lock = Lock()

    # Order Status, if order is not filled we will release the locks
    max_time_order_fill = UserInputs.max_wait_time_for_order_fill
    sleep_order_status_update = 2

    # File
    cas_tab_csv_file_path = UserInputs.cas_tab_csv_file_path

    # Custom column json file
    custom_columns_json_csv_file_path = UserInputs.custom_columns_json_csv_file_path

    ######## Order LOCKING #####################

    disconnect_time = 120
    sleep_five_sec = 5

    all_conid_from_con_details = {}
    map_expiry_to_conid = {}
    map_req_id_to_fut_fop_exchange = {}
    map_reqid_to_trading_class_sec_def = {}
    map_req_id_to_historical_data_dataframe = {}

    # Columns for Historical Data
    historical_data_columns = ["Time", "Open", "Close", "Volume"]

    # Column names, for each leg
    leg_columns = [
        "Unique ID",
        "Action",
        "SecType",
        "Symbol",
        "DTE",
        "Delta",
        "Right",
        "#Lots",
        "Lot Size",
        "Exchange",
        "Trading Class",
        "Currency",
        "ConID",
        "Primary Exchange",
        "Strike",
        "Expiry",
    ]

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

    #########  Positions  #########
    map_unique_id_to_positions = {}

    # map unique id to trade rm chek details
    map_unique_id_to_trade_rm_check_details = {}

    ######  C. A. S. Table ########
    # Inside set inside main, (run_high_low_price) these couneter are used inside the loop,
    # when counter hits the desired values the cas values are fetched again from the TWS, also present in screen_gui(when new combo is created setting values to 10**10)
    counter_long_term_value = 10**10
    counter_intra_day_value = 10**10
    counter_hv_related_value = 10**10
    counter_volume_related_value = 10**10
    counter_support_resistance_and_relative_fields_value = 10**10
    counter_accounts_value = 10**10
    counter_trade_rm_checks = 10**10
    counter_atr_for_order = 10**10
    counter_filter_condition = 0
    counter_candle_for_order = 10**10

    flag_update_long_term_value = False
    flag_update_intra_day_value = False
    flag_update_hv_related_value = False
    flag_update_volume_related_value = False
    flag_update_support_resistance_and_relative_fields = False
    flag_update_atr_for_order = False
    flag_update_candle_for_order = False

    # Setting it inside ComboCreation, updating values when combo deleted
    cas_map_con_id_to_action_type_and_combo_type = (
        {}
    )  # conid : {'BUY': { '1H': 0, '1D': 0} , 'SELL': { '1H': 0, '1D': 0}}

    # Setting it inside CAS SCREEN module(after condition is satisfied), updating values when combo deleted
    cas_conditional_legs_map_con_id_to_action_type_and_combo_type = (
        {}
    )  # conid : {'BUY': { '1H': 0, '1D': 0} , 'SELL': { '1H': 0, '1D': 0}}

    # Number of days for which the values in CAS(Conditional Add or Switch) are computed
    cas_number_of_days = UserInputs.cas_number_of_days

    # Number of days for which the value of ATR will be calculated
    atr_number_of_days = UserInputs.atr_number_of_days

    # number of buckets for relative atr in range
    relative_atr_in_range_number_of_buckets = (
        UserInputs.relative_atr_in_range_number_of_buckets
    )

    # flag for realtive atr in rnage
    flag_relative_atr_in_range = UserInputs.flag_relative_atr_in_range

    # Time interval after which the CAS(Conditional Add or Switch) values will be updated
    cas_long_term_fields_update_interval = (
        UserInputs.cas_long_term_fields_update_interval
    )  # Seconds
    cas_intraday_fields_update_interval = (
        UserInputs.cas_intraday_fields_update_interval
    )  # Seconds
    hv_related_fields_update_interval_time = (
        UserInputs.hv_related_fields_update_interval_time
    )  # Seconds
    volume_related_fields_update_interval_time = (
        UserInputs.volume_related_fields_update_interval_time
    )
    support_resistance_and_relative_fields_update_interval_time = (
        UserInputs.support_resistance_and_relative_fields_update_interval_time
    )
    account_table_update_interval = UserInputs.account_table_update_interval
    account_table_update_interval = UserInputs.account_table_update_interval
    rm_checks_interval_if_failed = UserInputs.rm_checks_interval_if_failed
    trade_rm_check_update_interval = UserInputs.trade_rm_check_update_interval
    atr_for_order_interval = UserInputs.atr_for_order_interval
    filter_conditions_update_interval = UserInputs.filter_conditions_update_interval
    candle_for_order_interval = UserInputs.candle_for_order_interval

    map_con_id_to_rule_id = {}
    map_rule_id_to_increments = {}
    map_con_id_to_contract = {}
    map_unique_id_to_n_day_high_low = {}
    map_unique_id_to_intraday_high_low = {}
    map_unique_id_to_long_term_high_low = {}
    map_unique_id_to_hv_related_values = {}
    map_unique_id_to_volume_related_fields = {}
    map_unique_id_to_atr_for_order_values = {}
    map_unique_id_to_candle_for_order_values = {}
    map_unique_id_to_leg_combo_comparision_val = {}
    map_unique_id_to_support_resistance_and_relative_fields = {}
    map_reqid_to_all_trading_class = {}
    map_unique_id_to_ladder_ids_list = {}
    map_ladder_id_to_ladder_obj = {}
    # map_sequence_id_to_sequnce_obj = {}  # todo remove
    map_ladder_id_to_sequence_ids_list = {}
    map_sequence_id_to_order_details = {}
    map_req_id_to_account_id_and_cond_id = {}
    map_account_id_and_con_id_to_pnl = {}
    map_unique_id_to_legs_unique_id = {}

    # CAS LongTerm Days
    cas_n_days = cas_number_of_days

    # ATR Days
    n_day_atr = atr_number_of_days

    # Duration Size and Bar size for support and resistance and all the relative values (rel atr, rel chg etc)
    support_resistance_and_relative_fields_look_back_days = (
        UserInputs.support_resistance_and_relative_fields_look_back_days
    )
    support_resistance_and_relative_fields_candle_size = (
        UserInputs.support_resistance_and_relative_fields_candle_size
    )

    # candle size mins for volume for trade rm check
    trade_level_rm_check_volume_candle_size = CandleSize.ONE_MIN  # Default parameter

    # lookback mins mins for volume for trade rm check
    trade_level_rm_check_volume_lookback_mins = (
        UserInputs.trade_level_rm_check_volume_lookback_mins
    )

    # threshold for volume trade level RM check
    volume_threshold_trade_rm_check = UserInputs.volume_threshold_trade_rm_check

    # candle size for volume magnet
    volume_magnet_candle_size = UserInputs.volume_magnet_candle_size

    # max lookback days fr volume magnet
    volume_magnet_max_lookback_days = UserInputs.volume_magnet_max_lookback_days

    # volume magnet lookback we checked
    volume_magnet_final_lookback_days = 0

    # ytiestamp for volume magnet
    volume_magnet_time_stamp = {}

    # threshold for bid ask spread trade level RM check
    bid_ask_spread_threshold_trade_rm_check = (
        UserInputs.bid_ask_spread_threshold_trade_rm_check
    )

    # threshold for bid ask qty trade level RM check
    bid_ask_qty_threshold_trade_rm_check = (
        UserInputs.bid_ask_qty_threshold_trade_rm_check
    )

    # range for support and threshold
    support_resistance_range_percent = UserInputs.support_resistance_range_percent

    # CAS Table Coulmns
    cas_table_columns_name_heading = [
        ("Unique ID", "Unique ID"),
        ("Tickers", "Tickers"),
        ("Buy Price", "Buy Price"),
        ("Sell Price", "Sell Price"),
        ("Total Abs Cost", "Total Abs\n      Cost"),
        ("Day High", "Day High"),
        ("Intraday High Time", " Intraday\nHigh Time"),
        ("Day Low", "Day Low"),
        ("Intraday Low Time", " Intraday\nLow Time"),
        ("Day Range Abs", "Day Range\n     Abs"),
        ("Day Range %", "Day Range %"),
        ("Close Price", "Close Price"),
        ("Chg Close%", "Chg Close%"),
        ("Chg Open%", "Chg Open%"),
        ("Chg Close", "Chg Close"),
        ("Chg Open", "Chg Open"),
        ("Opening Gap%", "Opening Gap%"),
        (f"N-Day High", f"{cas_n_days}-Day\n  High"),
        (f"N-Day Low", f"{cas_n_days}-Day\n  Low"),
        (f"N-Day Range Abs", f"   {cas_n_days}-Day\nRange Abs"),
        (f"N-Day Range %", f"  {cas_n_days}-Day\nRange %"),
        (f"K-Day ATR", f"{n_day_atr}-Day ATR"),
        ("HV Ann", "HV Ann"),
        ("Candle Volatility [CV]", "     Candle \nVolatility [CV]"),
        ("Chg Open %/ HV", "Chg Open %\n          /HV"),
        ("CV / Chg Open %", "       CV / \nChg Open %"),
        (
            "Q-Day Resistance",
            f"  {support_resistance_and_relative_fields_look_back_days}-Day \nResistance",
        ),
        (
            "Q-Day Support",
            f" {support_resistance_and_relative_fields_look_back_days}-Day \nSupport",
        ),
        (
            "Q-Day Resistance Count",
            f"{support_resistance_and_relative_fields_look_back_days}-Day Resistance\n       Count",
        ),
        (
            "Q-Day Support Count",
            f"{support_resistance_and_relative_fields_look_back_days}-Day Support\n       Count",
        ),
        ("Intraday Resistance", "  Intraday\nResistance"),
        ("Intraday Support", "Intraday\nSupport"),
        ("Intraday Resistance Count", "Intraday Resistance\n       Count"),
        ("Intraday Support Count", "Intraday Support\n      Count"),
        ("Average Volume", "Average \nVolume"),
        ("Volume +1 STD", "Volume \n+1 STD"),
        ("Volume -1 STD", "Volume \n-1 STD"),
        ("Volume +2 STD", "Volume \n+2 STD"),
        ("Volume -2 STD", "Volume \n-2 STD"),
        ("Volume +3 STD", "Volume \n+3 STD"),
        ("Volume -3 STD", "Volume \n-3 STD"),
        ("Rel ATR", "Rel ATR"),
        ("Rel Chg", "Rel Chg"),
        ("Rel Volume", "Rel Volume"),
        ("Rel Volume / Rel ATR", "Rel Volume \n  / Rel ATR"),
        ("Rel Chg / Rel Volume", "Rel Chg /\n Rel Volume"),
        ("Rel Chg / Rel ATR", "Rel Chg /\n Rel ATR"),
        ("[ATR/Abs Cost] / Low", "[ATR/Abs Cost]\n       / Low"),
        ("[ATR/Abs Cost] / High", "[ATR/Abs Cost]\n       / High"),
        ("Beta", "Beta"),
        ("Change From High%", "Change From\n       High%"),
        ("Change From Low%", "Change From\n       Low%"),
        ("Highest Price Comparison", "Highest Price\n Comparison"),
        ("Lowest Price Comparison", "Lowest Price\nComparison"),
        ("Price Range Ratio", "Price Range\n      Ratio"),
        ("Rel Volume / Rel Chg [Last N Minutes]", "     RV / RC\n[Last N Mins]"),
        ("Relative Volume On Positive Candles", "Rel Volume\n + Candles"),
        ("Relative Volume On Negative Candles", "Rel Volume\n  - Candles"),
        ("Relative ATR On Positive Candles", "   Rel ATR\n+ Candles"),
        ("Relative ATR On Negative Candles", "   Rel ATR\n- Candles"),
        ("Avg Bid-Ask / Avg Chg", "Avg Bid-Ask/\n    Avg Chg"),
        ("Current Bid-Ask / Avg Chg", "Bid-Ask/\nAvg Chg"),
        ("Relative Volume Derivative", "Rel Volume\n Derivative"),
        ("Relative ATR Derivative", "   Rel ATR\n Derivative"),
        ("Support - Price", "Support -\n   Price"),
        ("Resistance - Price", "Resistance -\n      Price"),
        ("Intraday Support - Price", "Intra Support -\n        Price"),
        ("Intraday Resistance - Price", "Intra Resistance\n         - Price"),
        ("Rel Volume / Opening Gap%", "   Rel Volume/\nOpening Gap%"),
        ("Volume Magnet", "Volume\nMagnet"),
        ("Relative ATR Lower", "Rel ATR\n  Lower"),
        ("Relative ATR Higher", "Rel ATR\n Higher"),
        ("Relative Volume Lower", "Rel Volume\n     Lower"),
        ("Relative Volume Higher", "Rel Volume\n     Higher"),
    ]

    cas_table_columns = [col_name for col_name, x in cas_table_columns_name_heading]

    # List of secondary columns in CAS table
    map_secondary_columns_to_expression_in_cas_table = {}

    # Getting columns for cache table from CAS table columns
    cache_data_table_columns = [
        col_name for col_name, x in cas_table_columns_name_heading
    ]

    # So that when the table is created the unique is is INT NOT NULL, and Tickers is VARCHAR(400)
    unqiue_id_col_name_for_cache = cache_data_table_columns[0]
    tickers_col_name_for_cache = cache_data_table_columns[1]

    # CAS table conditions list
    cas_table_fields_for_condition = cas_table_columns[2:] + [
        "Price Increase By",
        "Price Decrease By",
        "Price Adverse Chg By",
        "Price Favorable Chg By",
    ]

    cas_table_fields_for_condition = sorted(cas_table_fields_for_condition)
    cas_table_operators_for_condition = [
        "( )",
        "+",
        "-",
        "*",
        "/",
        ">",
        "<",
        "==",
        "!=",
        ">=",
        "<=",
        "and",
        "or",
    ]

    # CAS table expression list
    cas_table_fields_for_expression = cas_table_columns[2:]

    cas_table_fields_for_expression = sorted(cas_table_fields_for_expression)
    cas_table_operators_for_expression = [
        "( )",
        "+",
        "-",
        "*",
        "/",
        ">",
        "<",
        "==",
        "!=",
        ">=",
        "<=",
        "and",
        "or",
    ]

    # Allowed Tokens in CAS Conditions ( along with numbers)
    set_allowed_tokens = set(
        [
            x
            for x in cas_table_fields_for_condition
            + cas_table_operators_for_condition[1:]
        ]
    )
    set_allowed_tokens.add("(")
    set_allowed_tokens.add(")")

    cas_table_values_df = None  # Set and updated in prices
    map_cas_column_name_to_index = {key: i for i, key in enumerate(cas_table_columns)}
    cas_table_sort_by_column = {
        "Unique ID": False
    }  # Column, Reverse:True/False (True means reverse order, Flase means not in reverse) by default sort by unique ID

    # Will contain cas combo_obj mapped to unique_id
    cas_unique_id_to_combo_obj = {}

    # Ib Algo Mkt Order
    # 200, 201, 321, 387, 478, 10043, 10045, following are the different error codes that are received, when sending non compatiable IB Algo Orders
    flag_unique_id_supports_ib_algo = {}  # do unique id supports IB Algo Order
    map_order_id_to_ib_algo_order = (
        {}
    )  # It will be used inside error callback and the IB Algo Order sending
    ib_algo_priority = UserInputs.ib_algo_priority

    # Do the conid supports the IB Algo Order
    map_con_id_to_flag_supports_ib_algo_order = {}

    # HV Related User Inputs
    hv_method = UserInputs.hv_method
    hv_look_back_days = UserInputs.hv_look_back_days  # Days
    hv_candle_size = UserInputs.hv_candle_size  # mins

    # Volume Related User Inputs
    volume_related_fileds_look_back_days = (
        UserInputs.volume_related_fileds_look_back_days
    )
    volume_related_fileds_candle_size = UserInputs.volume_related_fileds_candle_size

    # lookback mins for relative vollume derivative
    relative_volume_derivation_lookback_mins = (
        UserInputs.relative_volume_derivation_lookback_mins
    )  # In minutes

    relative_atr_derivation_lookback_mins = (
        UserInputs.relative_atr_derivation_lookback_mins
    )

    # Last n minutes fields User Inputs

    last_n_minutes_fields_candle_size = UserInputs.last_n_minutes_fields_candle_size
    last_n_minutes_fields_lookback_days = UserInputs.last_n_minutes_fields_lookback_days

    # Cache Lookback Period
    lookback_period_for_cache = UserInputs.lookback_period_for_cache  # In Minutes

    # Calculating min in candle for annualized H. V. Calculation
    numeric_candle_data, time_frame = hv_candle_size.value.split()
    hv_mins_in_candle = (
        int(float(numeric_candle_data))
        if "min" in time_frame
        else int(float(numeric_candle_data)) * 60
    )

    # lookback days for order parameter atr
    order_parameter_atr_lookback_days = UserInputs.order_parameter_atr_lookback_days

    # candle size for order parameter atr
    order_parameter_atr_candle_size = UserInputs.order_parameter_atr_candle_size

    # candle size for order parameter candle
    order_parameter_candle_candle_size = UserInputs.order_parameter_candle_candle_size

    # flag for range orders
    flag_range_order = UserInputs.flag_range_order  # Intraday, Week, Month

    date_time_regex = r"\d{8} \d{2}:\d{2}:\d{2}"  # 20230503 15:00:00
    time_regex = r"\d{2}:\d{2}:\d{2}"  # 15:00:00

    # Number of days
    trading_days = 255
    hours_in_day = 24
    minutes_in_hour = 60

    # Convert the duration to minutes
    minutes_in_year = trading_days * hours_in_day * minutes_in_hour

    # TODO
    # When user edits combination the order type for exiting the positions
    edit_combo_exit_position_order_type = "Market"
