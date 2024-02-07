"""
Created on 14-Mar-2023

@author: Karan
"""


from com import *
from com.variables import *
from com.ibapi_callbacks import *
from com.contracts import *
from com.prices import *
from com.mysql_io import *
from com.order_execution import *
from com.combination_helper import *
from com.screen_gui import ScreenGUI
from com.screen_watchlist_manager import insert_all_watchlists_in_watchlists_table
from com.order_status import *
from com.positions import *
from com.high_low_price_calculator import *
from com.volume_and_change_related_columns import VolumeRelated
from com.fiilter_tab_helper import update_filter_condition_values
from com.high_low_cal_helper import *
from com.screen_scale_trader_manager import *
from com.screen_custom_columns import *
from com.json_io_custom_columns import *
from com.json_io_leg_to_combo_columns import *
from com.trade_level_rm_check import *

# Method to run app
def run_loop(app):
    app.run()


# Method to update account conditions table
def update_account_conditions():

    while True:

        # Update table
        variables.screen.screen_accounts_obj.update_accounts_table()

        # Check if time counter value is more than interval time
        if variables.counter_accounts_value > variables.account_table_update_interval:

            variables.flag_pnl_single = True

            # get postions for tickers mapped to accounts
            variables.app.reqPositions()

            # start time measure
            start = time.perf_counter()

            # Get update values and run RM checks
            get_updated_account_values()

            # Get time from start checkpoint
            time_took = int(time.perf_counter() - start)

            # set value to counter
            variables.counter_accounts_value = time_took
            variables.counter_trade_rm_checks += time_took

            # set value to counter
            variables.counter_filter_condition += time_took
            # print(f"Liquation mode flags = {variables.flag_account_liquidation_mode}")

            # Update GUI table
            variables.screen.screen_accounts_obj.update_accounts_table()

        # Check if time counter value is more than interval time
        if variables.counter_trade_rm_checks > variables.trade_rm_check_update_interval:

            # start time measure
            start = time.perf_counter()
            try:

                trade_level_rm_check_func()

            except Exception as e:

                # print to console
                if variables.flag_debug_mode:

                    print(f"Exception inside running trade rm checks, Exp: {e}")

            # print(f"Trade level RM flags = {variables.flag_trade_level_rm_checks}")

            # Get time from start checkpoint
            time_took = int(time.perf_counter() - start)

            # set value to counter
            variables.counter_trade_rm_checks = time_took
            # set value to counter
            variables.counter_accounts_value += time_took

            # set value to counter
            variables.counter_filter_condition += time_took

            # set value to True
            variables.flag_account_checks_completed_first_time = True
            variables.flag_account_checks_completed_wait = True

        # Check if time counter value is more than interval time
        if (
            variables.counter_filter_condition
            > variables.filter_conditions_update_interval
        ):

            # start time measure
            start = time.perf_counter()
            try:

                # run filter conditions
                update_filter_condition_values(variables.cas_table_values_df)

                # Set flag to true
                variables.flag_update_tables_watchlist_changed = True

                # print(variables.unique_ids_list_of_passed_condition)
            except Exception as e:

                # print to console
                if variables.flag_debug_mode:
                    print(f"Exception inside running trade rm checks, Exp: {e}")

            # Get time from start checkpoint
            time_took = int(time.perf_counter() - start)

            # set value to counter
            variables.counter_filter_condition = time_took

            # set value to counter
            variables.counter_trade_rm_checks += time_took

            # set value to counter
            variables.counter_accounts_value += time_took

        # Sleep
        time.sleep(1)

        # Increment value of counter by 1
        variables.counter_accounts_value += 1
        variables.counter_trade_rm_checks += 1
        variables.counter_filter_condition += 1


# Method to constantly check for updates in order status
def scale_trade_order_update():

    while True:
        update_order_status_for_scale_trade()
        time.sleep(1)

# Method to calculate price in interval
def run_high_low_price():

    # Init
    variables.flag_high_low_price_running = True
    long_term_update_interval_time = variables.cas_long_term_fields_update_interval
    intraday_update_interval_time = variables.cas_intraday_fields_update_interval
    hv_related_fields_update_interval_time = (
        variables.hv_related_fields_update_interval_time
    )
    volume_related_fields_update_interval_time = (
        variables.volume_related_fields_update_interval_time
    )
    price_and_volume_related_fields_update_interval_time = (
        variables.support_resistance_and_relative_fields_update_interval_time
    )
    atr_for_order_interval = variables.atr_for_order_interval
    candle_for_order_interval = variables.candle_for_order_interval

    sleep_interval_time = variables.sleep_time_between_iters  # 1 sec

    # Init Object
    high_low_price_obj = HighLowCalculator()
    volume_related_obj = VolumeRelated()

    # Making it available to class
    variables.high_low_price_obj = high_low_price_obj

    # Initiate flag for counter reset
    flag_counter_for_values_reset = False

    # Keep updating the cas values
    while variables.screen:

        # Init
        long_term_update_interval_time = variables.cas_long_term_fields_update_interval
        intraday_update_interval_time = variables.cas_intraday_fields_update_interval
        hv_related_fields_update_interval_time = (
            variables.hv_related_fields_update_interval_time
        )
        volume_related_fields_update_interval_time = (
            variables.volume_related_fields_update_interval_time
        )
        price_and_volume_related_fields_update_interval_time = (
            variables.support_resistance_and_relative_fields_update_interval_time
        )
        atr_for_order_interval = variables.atr_for_order_interval
        candle_for_order_interval = variables.candle_for_order_interval

        sleep_interval_time = variables.sleep_time_between_iters

        # So the motive was if ever a new combination is added in the system all the values longterm, intraday, HV realted, Volume realted
        # must be featched and updated in the same sequence that is why we have the big if statement that we have below being repeated multiple times

        # Recompute all the values
        if variables.flag_update_long_term_value:
            variables.counter_long_term_value = (
                variables.counter_intra_day_value
            ) = (
                variables.counter_hv_related_value
            ) = variables.counter_volume_related_value = (10**10)
            variables.counter_support_resistance_and_relative_fields_value = (
                variables.counter_atr_for_order
            ) = (10**10)


            variables.counter_candle_for_order = 10**10
            variables.flag_update_candle_for_order = False

            variables.flag_update_long_term_value = (
                variables.flag_update_intra_day_value
            ) = False
            variables.flag_update_hv_related_value = (
                variables.flag_update_volume_related_value
            ) = False
            (
                variables.flag_update_support_resistance_and_relative_fields,
                variables.flag_update_atr_for_order,
            ) = (False, False)
            continue

        # Update LongTerm values
        if variables.flag_update_long_term_value or (
            variables.counter_long_term_value
            >= (long_term_update_interval_time / sleep_interval_time)
        ):

            start = time.perf_counter()
            high_low_price_obj.update_long_term_values()

            time_took = int(time.perf_counter() - start)

            # Current time in the target time zone
            variables.lut_for_long_term_values = datetime.datetime.now(
                variables.target_timezone_obj
            )

            # Print to console
            if variables.flag_debug_mode:
                print(f"Time Took for Longterm Values: {time_took}")

            variables.counter_intra_day_value += int(time_took / sleep_interval_time)
            variables.counter_hv_related_value += int(time_took / sleep_interval_time)
            variables.counter_volume_related_value += int(
                time_took / sleep_interval_time
            )
            variables.counter_support_resistance_and_relative_fields_value += int(
                time_took / sleep_interval_time
            )
            variables.counter_atr_for_order += int(time_took / sleep_interval_time)
            variables.counter_candle_for_order += int(
                time_took / sleep_interval_time
            )
            variables.counter_long_term_value = 0
            variables.flag_update_long_term_value = False

        # Recompute all the values
        if variables.flag_update_intra_day_value:
            variables.counter_long_term_value = (
                variables.counter_intra_day_value
            ) = (
                variables.counter_hv_related_value
            ) = variables.counter_volume_related_value = (10**10)
            variables.counter_support_resistance_and_relative_fields_value = (
                variables.counter_atr_for_order
            ) = (10**10)

            variables.counter_candle_for_order = 10 ** 10
            variables.flag_update_candle_for_order = False

            variables.flag_update_long_term_value = (
                variables.flag_update_intra_day_value
            ) = False
            variables.flag_update_hv_related_value = (
                variables.flag_update_volume_related_value
            ) = False
            (
                variables.flag_update_support_resistance_and_relative_fields,
                variables.flag_update_atr_for_order,
            ) = (False, False)
            continue

        # Update IntraDay values
        if variables.flag_update_intra_day_value or (
            variables.counter_intra_day_value
            >= (intraday_update_interval_time / sleep_interval_time)
        ):

            start = time.perf_counter()
            high_low_price_obj.update_intraday_values()
            time_took = int(time.perf_counter() - start)

            # Current time in the target time zone
            variables.lut_for_intraday_values = datetime.datetime.now(
                variables.target_timezone_obj
            )

            # Print to console
            if variables.flag_debug_mode:
                print(f"Time Took for IntraDay Values: {time_took}")

            variables.counter_intra_day_value += int(time_took / sleep_interval_time)
            variables.counter_hv_related_value += int(time_took / sleep_interval_time)
            variables.counter_volume_related_value += int(
                time_took / sleep_interval_time
            )
            variables.counter_support_resistance_and_relative_fields_value += int(
                time_took / sleep_interval_time
            )
            variables.counter_atr_for_order += int(time_took / sleep_interval_time)
            variables.counter_candle_for_order += int(
                time_took / sleep_interval_time
            )
            variables.counter_intra_day_value = 0
            variables.flag_update_intra_day_value = False

        # Recompute all the values
        if variables.flag_update_hv_related_value:
            variables.counter_long_term_value = (
                variables.counter_intra_day_value
            ) = (
                variables.counter_hv_related_value
            ) = variables.counter_volume_related_value = (10**10)
            variables.counter_support_resistance_and_relative_fields_value = (
                variables.counter_atr_for_order
            ) = (10**10)

            variables.counter_candle_for_order = 10 ** 10
            variables.flag_update_candle_for_order = False

            variables.flag_update_long_term_value = (
                variables.flag_update_intra_day_value
            ) = False
            variables.flag_update_hv_related_value = (
                variables.flag_update_volume_related_value
            ) = False
            (
                variables.flag_update_support_resistance_and_relative_fields,
                variables.flag_update_atr_for_order,
            ) = (False, False)
            continue



        # Update HV Related values
        if variables.flag_update_hv_related_value or (
            variables.counter_hv_related_value
            >= (hv_related_fields_update_interval_time / sleep_interval_time)
        ):

            start = time.perf_counter()
            high_low_price_obj.calculate_hv_related_columns()
            time_took = int(time.perf_counter() - start)

            # Current time in the target time zone
            variables.lut_for_long_term_values = datetime.datetime.now(
                variables.target_timezone_obj
            )

            # Print to console
            if variables.flag_debug_mode:
                print(f"Time Took for HV Related Values: {time_took}")

            variables.counter_intra_day_value += int(time_took / sleep_interval_time)
            variables.counter_hv_related_value += int(time_took / sleep_interval_time)
            variables.counter_volume_related_value += int(
                time_took / sleep_interval_time
            )
            variables.counter_support_resistance_and_relative_fields_value += int(
                time_took / sleep_interval_time
            )
            variables.counter_atr_for_order += int(time_took / sleep_interval_time)
            variables.counter_candle_for_order += int(
                time_took / sleep_interval_time
            )
            variables.counter_hv_related_value = 0
            variables.flag_update_hv_related_value = False

        # Recompute all the values
        if variables.flag_update_volume_related_value:
            variables.counter_long_term_value = (
                variables.counter_intra_day_value
            ) = (
                variables.counter_hv_related_value
            ) = variables.counter_volume_related_value = (10**10)
            variables.counter_support_resistance_and_relative_fields_value = (
                variables.counter_atr_for_order
            ) = (10**10)

            variables.counter_candle_for_order = 10 ** 10
            variables.flag_update_candle_for_order = False

            variables.flag_update_long_term_value = (
                variables.flag_update_intra_day_value
            ) = False
            variables.flag_update_hv_related_value = (
                variables.flag_update_volume_related_value
            ) = False
            (
                variables.flag_update_support_resistance_and_relative_fields,
                variables.flag_update_atr_for_order,
            ) = (False, False)
            continue

        # Update Volume Related values
        if variables.flag_update_volume_related_value or (
            variables.counter_volume_related_value
            >= (volume_related_fields_update_interval_time / sleep_interval_time)
        ):

            start = time.perf_counter()
            volume_related_obj.update_volume_related_fields()
            time_took = int(time.perf_counter() - start)

            # Current time in the target time zone
            variables.lut_for_volume_related_fields = datetime.datetime.now(
                variables.target_timezone_obj
            )

            # Print to console
            if variables.flag_debug_mode:
                print(f"Time Took for Volume Related Values: {time_took}")

            variables.counter_intra_day_value += int(time_took / sleep_interval_time)
            variables.counter_hv_related_value += int(time_took / sleep_interval_time)
            variables.counter_volume_related_value += int(
                time_took / sleep_interval_time
            )
            variables.counter_support_resistance_and_relative_fields_value += int(
                time_took / sleep_interval_time
            )
            variables.counter_atr_for_order += int(time_took / sleep_interval_time)
            variables.counter_candle_for_order += int(
                time_took / sleep_interval_time
            )
            variables.counter_volume_related_value = 0
            variables.flag_update_volume_related_value = False



        # Recompute all the values
        if variables.flag_update_atr_for_order:
            variables.counter_long_term_value = (
                variables.counter_intra_day_value
            ) = (
                variables.counter_hv_related_value
            ) = variables.counter_volume_related_value = (10**10)
            variables.counter_support_resistance_and_relative_fields_value = (
                variables.counter_atr_for_order
            ) = (10**10)

            variables.counter_candle_for_order = 10 ** 10
            variables.flag_update_candle_for_order = False

            variables.flag_update_long_term_value = (
                variables.flag_update_intra_day_value
            ) = False
            variables.flag_update_hv_related_value = (
                variables.flag_update_volume_related_value
            ) = False
            (
                variables.flag_update_support_resistance_and_relative_fields,
                variables.flag_update_atr_for_order,
            ) = (False, False)
            continue

        # Update LongTerm values
        if variables.flag_update_atr_for_order or (
            variables.counter_atr_for_order
            >= (atr_for_order_interval / sleep_interval_time)
        ):

            start = time.perf_counter()
            high_low_price_obj.calculate_atr_for_order()

            time_took = int(time.perf_counter() - start)

            # Current time in the target time zone
            variables.lut_for_long_term_values = datetime.datetime.now(
                variables.target_timezone_obj
            )

            # Print to console
            if variables.flag_debug_mode:
                print(f"Time Took for ATR for order Values: {time_took}")

            variables.counter_long_term_value += int(time_took / sleep_interval_time)
            variables.counter_intra_day_value += int(time_took / sleep_interval_time)
            variables.counter_hv_related_value += int(time_took / sleep_interval_time)
            variables.counter_volume_related_value += int(
                time_took / sleep_interval_time
            )
            variables.counter_support_resistance_and_relative_fields_value += int(
                time_took / sleep_interval_time
            )
            variables.counter_candle_for_order += int(
                time_took / sleep_interval_time
            )

            variables.flag_update_atr_for_order = False
            variables.counter_atr_for_order = 0

        # Recompute all the values
        if variables.flag_update_candle_for_order:
            variables.counter_long_term_value = (
                variables.counter_intra_day_value
            ) = (
                variables.counter_hv_related_value
            ) = variables.counter_volume_related_value = (10 ** 10)
            variables.counter_support_resistance_and_relative_fields_value = (
                variables.counter_atr_for_order
            ) = (10 ** 10)

            variables.counter_candle_for_order = 10 ** 10
            variables.flag_update_candle_for_order = False

            variables.flag_update_long_term_value = (
                variables.flag_update_intra_day_value
            ) = False
            variables.flag_update_hv_related_value = (
                variables.flag_update_volume_related_value
            ) = False
            (
                variables.flag_update_support_resistance_and_relative_fields,
                variables.flag_update_atr_for_order,
            ) = (False, False)
            continue

        # Update LongTerm values
        if variables.flag_update_candle_for_order or (
                variables.counter_candle_for_order
                >= (candle_for_order_interval / sleep_interval_time)
        ):

            start = time.perf_counter()
            high_low_price_obj.get_last_candle_for_order()

            time_took = int(time.perf_counter() - start)

            # Current time in the target time zone
            variables.lut_for_long_term_values = datetime.datetime.now(
                variables.target_timezone_obj
            )

            # Print to console
            if variables.flag_debug_mode:
                print(f"Time Took for candle for order Values: {time_took}")

            variables.counter_long_term_value += int(time_took / sleep_interval_time)
            variables.counter_intra_day_value += int(time_took / sleep_interval_time)
            variables.counter_hv_related_value += int(time_took / sleep_interval_time)
            variables.counter_volume_related_value += int(
                time_took / sleep_interval_time
            )
            variables.counter_support_resistance_and_relative_fields_value += int(
                time_took / sleep_interval_time
            )
            variables.counter_candle_for_order = 0

            variables.flag_update_candle_for_order = False
            variables.counter_atr_for_order += int(
                time_took / sleep_interval_time
            )

        # Recompute all the values
        if variables.flag_update_support_resistance_and_relative_fields:
            variables.counter_long_term_value = (
                variables.counter_intra_day_value
            ) = (
                variables.counter_hv_related_value
            ) = variables.counter_volume_related_value = (10 ** 10)
            variables.counter_support_resistance_and_relative_fields_value = (
                variables.counter_atr_for_order
            ) = (10 ** 10)

            variables.counter_candle_for_order = 10 ** 10
            variables.flag_update_candle_for_order = False

            variables.flag_update_long_term_value = (
                variables.flag_update_intra_day_value
            ) = False
            variables.flag_update_hv_related_value = (
                variables.flag_update_volume_related_value
            ) = False
            (
                variables.flag_update_support_resistance_and_relative_fields,
                variables.flag_update_atr_for_order,
            ) = (False, False)
            continue

        # Updating Price based Relative indicators values
        if variables.flag_update_support_resistance_and_relative_fields or (
                variables.counter_support_resistance_and_relative_fields_value
                >= (
                        price_and_volume_related_fields_update_interval_time
                        / sleep_interval_time
                )
        ):

            start = time.perf_counter()
            volume_related_obj.get_volume_magnet_tiestamps()
            update_price_based_relative_indicators_values()
            time_took = int(time.perf_counter() - start)

            # Current time in the target time zone
            variables.lut_for_price_based_relative_indicators_values = (
                datetime.datetime.now(variables.target_timezone_obj)
            )

            # Print to console
            if variables.flag_debug_mode:
                print(f"Time Took for Price Based Relative Indicator: {time_took}")

            variables.counter_intra_day_value += int(time_took / sleep_interval_time)
            variables.counter_hv_related_value += int(time_took / sleep_interval_time)
            variables.counter_volume_related_value += int(
                time_took / sleep_interval_time
            )
            variables.counter_support_resistance_and_relative_fields_value += int(
                time_took / sleep_interval_time
            )
            variables.counter_atr_for_order += int(time_took / sleep_interval_time)
            variables.counter_candle_for_order += int(
                time_took / sleep_interval_time
            )
            variables.counter_support_resistance_and_relative_fields_value = 0
            variables.flag_update_support_resistance_and_relative_fields = False


        # Unset the variable dict here
        # # N days High And Low
        # variables.map_unique_id_to_long_term_high_low
        #
        # # HV Related Column
        # variables.map_unique_id_to_hv_related_values
        #
        # # Days Open, High Low
        # variables.map_unique_id_to_intraday_high_low
        #
        # # Volume Related columns
        # variables.map_unique_id_to_volume_related_fields
        #
        # # Both Price and Volume Related columns
        # variables.map_unique_id_to_support_resistance_and_relative_fields

        time.sleep(sleep_interval_time)
        variables.counter_long_term_value += 1
        variables.counter_intra_day_value += 1
        variables.counter_hv_related_value += 1
        variables.counter_volume_related_value += 1
        variables.counter_support_resistance_and_relative_fields_value += 1
        variables.counter_atr_for_order += 1
        variables.counter_candle_for_order += 1

    variables.flag_high_low_price_running = False

# Method to run main screen
def run_screen():

    # Create Screen GUI
    screen = ScreenGUI()

    # Expose screngui to all methods
    variables.screen = screen

    # Run the screen main loop, when close set 'variables.screen' as False
    variables.screen.window.mainloop()
    variables.screen = False

# Method to get accounts in current session
def get_trading_accounts():

    try:

        # Get list of trading accounts
        variables.app.reqManagedAccts()

    except Exception as e:

        # Print To console
        if variables.flag_debug_mode:

            print(f"Problem in getting trading accounts list")


if __name__ == "__main__":

    # Main App TWS Object
    app = IBapi()
    app.connect(
        variables.ibkr_tws_host,
        variables.ibkr_tws_port,
        variables.ibkr_tws_connection_id,
    )

    # CAS App TWS Object
    cas_app = IBapi()
    cas_app.connect(
        variables.ibkr_tws_host,
        variables.ibkr_tws_port,
        variables.ibkr_tws_connection_id_for_cas,
    )

    #########
    # First we are connecting CAS App, Then Main, app remember to set 'variables.nextorderId = None' after connecting CAS APP
    # Check def nextValidId(self, orderId: int) in ibapi_callbacks
    #########

    # Start the web socket in a thread CAS APP
    cas_api_thread = threading.Thread(target=run_loop, args=(cas_app,), daemon=True)
    cas_api_thread.start()

    # Check if the CAS APP is connected via order id
    while True:
        if isinstance(cas_app.nextorderId, int):
            print("CAS APP Connected")
            break
        else:
            print("CAS APP waiting for connection")
            time.sleep(1)

    # Setting it to None for Main APP
    variables.nextorderId = None

    # Start the web socket in a thread
    api_thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
    api_thread.start()

    # Check if the API is connected via order id
    while True:
        if isinstance(variables.nextorderId, int):
            print("Main APP Connected")
            break
        else:
            print("Main APP waiting for connection")
            time.sleep(1)

    # Expose app to all methods
    variables.app = app

    # Expose app to all methods
    variables.cas_app = cas_app

    # req_gap so that requests cant be same for CAS and Main App
    req_gap = 500_000

    # Making a difference of '500_000' between CAS App and Main App Request
    variables.cas_app.nextorderId = variables.nextorderId + req_gap

    # Print to console
    print(f"Main: {variables.nextorderId}, CAS APP: {variables.cas_app.nextorderId}")

    # Getting the trading Accounts
    get_trading_accounts()

    # Record module start time
    module_start_time = datetime.datetime.now(variables.target_timezone_obj)

    # Init order_specs_dict
    multileg_specs = dict()

    # List of legs in list,
    multileg_unique_id_list = dict()

    unique_id_to_combolegs_dict = {}

    # Getting beta contract
    if not get_beta_contract():
        if variables.flag_debug_mode:
            print(
                f"Unable to find the Beta Contract Symbol: {variables.index_select_for_beta_column}"
            )

        sys.exit(
            f"Unable to find the Beta Contract Symbol: {variables.index_select_for_beta_column}"
        )

    # Recovery Mode
    if variables.flag_recovery_mode:

        if variables.flag_debug_mode:
            print("\nSetting up recovery mode")
            print("Fetching order status (can take upto 10 seconds)")

        # Setup filter: all trades executed after strategy_start_time
        executionFilter = ExecutionFilter()
        eight_days_old_time = module_start_time - relativedelta(days=8)
        executionFilter.time = eight_days_old_time.strftime("%Y%m%d-%H:%M:%S")

        if variables.flag_debug_mode:
            print("executionFilter.time = ", executionFilter.time)

        # Get execution details
        get_execution_details(executionFilter)

        # Sleep for 10 secs
        time.sleep(variables.sleep_time_ten_seconds - 6)

        # Check all orders in the db, any order that has a last update time < module start time, mark those as cancelled
        # mark_order_cancelled(module_start_time)

        # Get all the active combinations from db (Active Combinations)
        all_legs_in_active_combinations_table = get_primary_vars_db(
            variables.sql_table_combination
        )

        # Creates and return combolegs dict, for further process (combo_creation and subscription)
        unique_id_to_combolegs_dict = get_unique_id_combolegs_dict(
            all_legs_in_active_combinations_table
        )

        # Pause all active ladder instances after restart
        pause_all_active_ladders_after_restart_db()

        # Cancel all pending order originated in scale trade after restart
        cancel_all_orders_from_scale_trade_after_restart_db()

        # Get all sequence objects from db
        ladder_id_to_sequence_obj_dict = get_sequence_obj_dict()

        # Get all ladder objects from db
        get_ladder_id_ladder_obj_dict(ladder_id_to_sequence_obj_dict)

    else:

        # Try Dropping Table, Create the Tables if  recovery_mode is False
        drop_tables()
        create_tables()

    # Create the cache table if the order does not match with the CAS Columns
    if check_if_cache_table_needs_to_be_recreated():

        # Print to console
        if variables.flag_debug_mode:
            print(f"CAS and Cache Columns are not same, Updating the cache table in db")

        # Print to console
        create_cache_table()
    else:

        # Print to console
        if variables.flag_debug_mode:
            print(f"CAS and Cache Columns are same, not updating the cache table in db")

    #### Secondary Indicators
    # Check if json file for custom columns exists
    check_if_json_file_exists()

    # Get max custom column id form JSON file
    get_custom_column_id_from_json()

    # check if json file for columns for leg to combo table is present
    check_if_json_file_exists_for_lts_columns()

    # Update secondary columns at start of app
    update_secondary_columns()

    # Start Screen Now
    screen_thread = threading.Thread(target=run_screen)
    screen_thread.start()

    # get the max present unique id from DB, min value if nothing is present will be "Zero"
    variables.unique_id = get_unique_id_db()

    # Increasing it so we can use it.
    variables.unique_id += 1

    # get the max present ladder id from DB, min value if nothing is present will be "Zero"
    variables.ladder_id = get_ladder_id_db()

    # Increasing it's value so we can use it.
    variables.ladder_id += 1

    # get the max present sequence_id id from DB, min value if nothing is present will be "Zero"
    variables.sequence_id = get_sequence_id_db()

    # Increasing it's value so we can use it.
    variables.sequence_id += 1

    # Method to update sclae trade orders after restart
    update_combination_status_in_db_and_order_book(flag_update_scale_trade_order=True)

    # Create Combinations, Subscribe Data, add them into the ScreenGUI
    for unique_id, legs_tuple_list in unique_id_to_combolegs_dict.items():

        combo_obj = create_combination(legs_tuple_list, input_from_db=True)

        # The combo that we are not able to insert again(expired)
        if type(combo_obj) == tuple:
            continue

        subscribe_mktdata_combo_obj(combo_obj)

    # Get last order book table cleared Time, insert only non-cleared orders in table.
    order_book_last_cleaned_time = get_order_book_cleaned_time()
    insert_combo_order_status_in_order_book(order_book_last_cleaned_time)

    # It gets all the legs from cas_legs_table and we those legs are saved in 'cas_unique_id_to_combo_obj' for viewing incremental tickers
    all_legs_in_cas_legs_table = get_primary_vars_db(variables.sql_table_cas_legs)

    # Creates and return combolegs dict, for further process (combo_creation, inserting in cas condition table and viewing)
    cas_unique_id_to_combolegs_dict = get_unique_id_combolegs_dict(
        all_legs_in_cas_legs_table
    )

    # Create Cas Combinations, add them into the ScreenGUI 'CAS Condition table',
    for unique_id, legs_tuple_list in cas_unique_id_to_combolegs_dict.items():

        cas_combo_object = create_combination(
            legs_tuple_list, input_from_db=True, input_from_cas_tab=True
        )



        # Add the cas combo to class variables.
        variables.cas_unique_id_to_combo_obj[unique_id] = cas_combo_object

        # what data do we need for the combo 1Day or 1H for CAS Correlation(N-Day) Longterm Values
        only_stk_fut = False

        # Checking Combo type, and map con_id to contract
        for leg_obj_ in cas_combo_object.buy_legs + cas_combo_object.sell_legs:

            if leg_obj_.sec_type in ["OPT", "FOP"]:
                only_stk_fut = False

            # Mapping con_id to contract
            variables.map_con_id_to_contract[leg_obj_.con_id] = leg_obj_.contract

        # Update the values of 'cas_conditional_legs_map_con_id_to_action_type_and_combo_type' used while getting HighLowCAS prices (for Correlation)
        for leg_obj_ in cas_combo_object.buy_legs + cas_combo_object.sell_legs:
            # Coind for leg
            conid = leg_obj_.con_id
            action = leg_obj_.action

            if (
                conid
                not in variables.cas_conditional_legs_map_con_id_to_action_type_and_combo_type
            ):
                variables.cas_conditional_legs_map_con_id_to_action_type_and_combo_type[
                    conid
                ] = {"BUY": {"1H": 0, "1D": 0}, "SELL": {"1H": 0, "1D": 0}}

            # Count which data is required how many times for CAS
            if only_stk_fut:
                variables.cas_conditional_legs_map_con_id_to_action_type_and_combo_type[
                    conid
                ][action]["1D"] += 1
            else:
                variables.cas_conditional_legs_map_con_id_to_action_type_and_combo_type[
                    conid
                ][action]["1H"] += 1

    # Insert the cas condition in the cas_condition table
    insert_cas_conditions_in_cas_conditions_table_from_db(only_pending=True)

    # Insert Watchlists in watchlist manager table
    insert_all_watchlists_in_watchlists_table()

    # Update account conditions tbale
    variables.screen.screen_accounts_obj.update_account_conditions_table()

    # Init account tab
    # Update table
    variables.screen.screen_accounts_obj.update_accounts_table()

    # Insert rows in custom column table
    variables.screen.screen_custom_columns_obj.update_custom_column_table()
    #### Secondary Indicators

    # Insert scale trades in scale trade table at start of app
    insert_all_scale_trades_in_scale_trader_table()

    # Creating separate thread
    scale_trade_order_update_thread = threading.Thread(
        target=scale_trade_order_update, daemon=True
    )
    scale_trade_order_update_thread.start()

    # Creating separate thread
    account_conditions_update_thread = threading.Thread(
        target=update_account_conditions, daemon=True
    )
    account_conditions_update_thread.start()

    # Creating a separate thread
    high_low_price_thread = threading.Thread(target=run_high_low_price, daemon=True)
    high_low_price_thread.start()

    # While Screen is open
    while variables.screen:
        try:

            # Added CAS Update here
            # print('here 2')
            update_prices_in_market_watch___reference_price_in_db_and_order_book__cas_table()
            # print('here 3')
            monitor_and_send_order()

            update_execution_engine_orders()
            # print('here 4')
            update_combination_status_in_db_and_order_book()
            # print('here 5')
            update_combo_positions_in_positions_tab()
            # print('here 6')
            monitor_and_trigger_cas_condition()

            variables.screen.screen_conditional_series_tab.monitor_conditional_series()
            # print('here 7')
            # print(f"Active Threads {threading.active_count()}")

            variables.screen.screen_portfolio_tab.update_portfolio_combo_table()
            variables.screen.screen_portfolio_tab.update_portfolio_legs_table()


            time.sleep(1)
        except Exception as e:

            if variables.flag_debug_mode:

                print(f"Inside While Screen is open block, Exp: {e}")

    if variables.flag_debug_mode:
        print("Disconnecting")

    # Joining the thread
    scale_trade_order_update_thread.join()
    high_low_price_thread.join()
    app.disconnect()
    cas_app.disconnect()
