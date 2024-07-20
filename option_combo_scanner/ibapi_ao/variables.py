import configparser
import os
from threading import Lock

import pytz

# Read the config file
config = configparser.ConfigParser()
# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
option_scanner_user_inputs_ini_file_path = os.path.join(script_dir, "..",  "..", "option_scanner_user_inputs.ini")

config.read(option_scanner_user_inputs_ini_file_path)

dbconfig = config["Database"]
# tws_config = config["TWS"]
timezone_config = config["TimeZone"]


class Variables(object):
    app = None

    # account_id = tws_config["account"]
    # user_trading_account = account_id

    map_order_id_to_order_status = {}
    map_wheel_id_to_wheel_obj = {}
    standard_currency_for_account_value = "USD"
    fetched_account_values_dataframe_columns = [
        "AccountID",
        "NetLiquidationByCurrency",
        "MaintMarginReq",
    ]
    flag_account_update_ended = {}
    map_account_id_to_maint_margin = {}
    map_account_id_to_nlv = {}
    all_active_trading_accounts = set()
    max_wait_time_for_executions = 60

    # TWS Settings
    # tws_host = tws_config["host"]
    # tws_port = int(tws_config["port"])
    # tws_client_id = int(tws_config["client_id"])
    # user_trading_account = tws_config["account"]

    # Time Zone
    target_timezone = timezone_config["target_timezone"]
    target_timezone_obj = pytz.timezone(target_timezone)

    # Last connection time with timezone
    last_tws_connection_time = None

    # Subscriptions
    map_unique_id_to_order_preset = {}
    map_unique_id_to_conid = {}
    map_conid_to_contract = {}
    map_conid_to_subscription_count = {}
    map_conid_to_subscripiton_req_id = {}

    # Flags
    flag_market_open = False
    flag_debug_mode = False
    flag_use_rth = 1  # Historical data
    flag_cancel_subscription = True  # Currently not being used anywhere, this is typically used when we make a call to reqMktData
    flag_snapshot_req_mkt_data = (
        False  # Use snapshot data for reqMktData calls for combos
    )
    flag_use_rth_und_data = False  # Use RTH only for real time bars for the underlying

    # Internal variables init
    nextorderId = None
    sleep_time_waiting_for_tws_response = 0.1  # Used when waiting for response from TWS
    sleep_time_db = 0.2
    sleep_time_ibkr_orders = 2
    sleep_time_between_iters = 1
    sleep_time_wait_bid_ask_legs = 10

    expiry_dates = {}
    strike_prices = {}
    contract_details = {}
    contract_details_end = {}
    options_delta_bid = {}
    options_delta_ask = {}
    options_delta = {}

    live_und_price = None

    # dict for storing price candle data
    bid_price = {}
    ask_price = {}
    high_price = {}
    low_price = {}
    close_price = {}
    implied_volatility = {}
    call_option_open_interest = {}
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

    order_type = "MKT"  # For Order Placement,
    multileg_bid_ask = {}

    ##########
    conid_mktdata_subscription_dict = {}
    con_id_to_req_id_dict = {}
    unique_id_to_combo_obj = {}
    unique_id_to_prices_dict = {}

    ######## Order LOCKING #####################

    # lock for tickers
    order_lock = {}

    # Lock on order sending
    order_sending_lock = Lock()

    # Order Status, if order is not filled we will release the locks
    sleep_order_status_update = 2

    # File

    ######## Order LOCKING #####################

    disconnect_time = 120
    sleep_five_sec = 5

    all_conid_from_con_details = {}
    map_expiry_to_conid = {}
    map_req_id_to_fut_fop_exchange = {}
    map_reqid_to_trading_class_sec_def = {}
    map_req_id_to_historical_data_dataframe = {}

    # Columns for Historical Data
    historical_data_columns = ["Time", "Open", "Close"]

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

    cas_table_fields_for_condition = ["Price", "Volume"]

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

    date_time_regex = r"\d{8} \d{2}:\d{2}:\d{2}"  # 20230503 15:00:00
    time_regex = r"\d{2}:\d{2}:\d{2}"  # 15:00:00

    # Number of days
    trading_days = 255
    hours_in_day = 24
    minutes_in_hour = 60

    # Convert the duration to minutes
    minutes_in_year = trading_days * hours_in_day * minutes_in_hour
