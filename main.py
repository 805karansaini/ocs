import warnings

# Ignore all warnings
warnings.filterwarnings("ignore")
import asyncio
import datetime
import os
import threading
import time
import tkinter as tk
import traceback
from tkinter import messagebox

# from option_combo_scanner.ibapi_ao.app import IBapi
from com.ibapi_callbacks import IBapi
from com.variables import variables as com_variables
from option_combo_scanner.client_app.app_v1 import AlgoOneAPI
from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.database.set_up_db import SetupDatabase
from option_combo_scanner.gui.gui import IsScreenRunning, ScreenGUI
from option_combo_scanner.gui.scanner_inputs_tab import ScannerInputsTab
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.recovery_mode import RecoveryMode
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.indicators_calculator.indicator_calculation import (
    IndicatorCalculation,
)
from option_combo_scanner.strategy.scanner import Scanner, run_option_combo_scanner
from option_combo_scanner.strategy.strategy_variables import StrategyVariables
from option_combo_scanner.strategy.utilities import StrategyUtils

logger = CustomLogger.logger


def run_indicator_thread():
    # While Screen is open
    while True:
        try:
            # Start Time
            start_time = time.time()

            IndicatorCalculation.compute_indicators()

            # End Time
            end_time = time.time()

            time_taken = end_time - start_time
            # print(f"Time taken to compute indicators: {time_taken} seconds")
        except Exception as e:
            logger.error(f"Exception in indicator thread loop: {e}")
            print(f"Exception in indicator thread loop: {e}")
            traceback.print_exc()

        # print("End of indicators Calculation")
        time.sleep(20)


# Method to run app
def run_loop(app):
    app.run()


if __name__ == "__main__":

    def run_screen():
        global screen

        # Create Screen GUI
        screen = ScreenGUI()

        # Run the screen main loop, when close set 'variables.screen' as False
        screen.window.mainloop()

        logger.debug("main.py run_screen: Screen Closed")

    # # Check if the user wants to delete the database
    flag_start_in_recovery_mode = StrategyVariables.flag_recovery_mode

    # Recovery Mode is False, start fresh
    if not flag_start_in_recovery_mode:
        SetupDatabase()

    # Module start time
    module_start_time = datetime.datetime.now(variables.target_timezone_obj)

    ######## Start New Data Server Integration Changes
    def start_loop(loop):
        asyncio.set_event_loop(loop)
        loop.run_forever()
        print("End in loop")

    # Create a new event loop and start it in a new thread
    new_loop = asyncio.new_event_loop()
    t = threading.Thread(target=start_loop, args=(new_loop,))
    t.start()

    time.sleep(1)

    access_token = "OCS123"
    print(f"Connecting to Data Server: {access_token}")
    # Creating the Data Server Client
    ds_client = AlgoOneAPI(
        data_server_host=StrategyVariables.ds_host,
        data_server_port=StrategyVariables.ds_port,
        data_server_client_id=StrategyVariables.ds_connection_id,
        loop=new_loop,
        access_token=access_token,
    )
    ds_client.start()

    # Wait for the connection
    while not ds_client.is_connected():
        time.sleep(0.2)
    ####### End New Data Server Integration Changes

    com_variables.ds_client = ds_client
    if com_variables.use_api_bridge:
        app = ds_client
        com_variables.app = app
        com_variables.cas_app = app

    else:
        # Main App TWS Object
        app = IBapi()
        app.connect(
            StrategyVariables.ibkr_tws_host,
            StrategyVariables.ibkr_tws_port,
            StrategyVariables.ibkr_tws_connection_id,
        )

        # Setting it to None for Main APP
        com_variables.nextorderId = None
        # Start the web socket in a thread
        api_thread = threading.Thread(target=run_loop, args=(app,), daemon=True)
        api_thread.start()

        # Check if the API is connected via order id
        while True:
            if isinstance(com_variables.nextorderId, int):
                print("Main APP Connected")
                break
            else:
                print("Main APP waiting for connection")
                time.sleep(1)

        # Expose app to all methods
        com_variables.app = app
        com_variables.cas_app = app

    # Start Screen Now
    screen_thread = threading.Thread(target=run_screen)
    screen_thread.start()

    # Wait for screen to start
    while not IsScreenRunning.flag_is_screen_running:
        logger.debug("Intializing GUI Screen")
        print("Intializing GUI Screen")
        time.sleep(0.5)
    else:
        time.sleep(0.5)

    StrategyVariables.screen = screen
    com_variables.screen = screen

    c = 0

    logger.debug("GUI Screen Initialized")
    print("GUI Screen Initialized")

    # Creating a separate thread
    scanner_thread = threading.Thread(target=run_option_combo_scanner, daemon=True)
    scanner_thread.start()

    indicator_thread = threading.Thread(target=run_indicator_thread, daemon=True)
    indicator_thread.start()

    # Creating the Scanner Object
    # scanner_input = ScannerInputsTab(scanners_object)
    # While Screen is open
    while IsScreenRunning.flag_is_screen_running:
        # print(f"\n\n# of Configs: {StrategyVariables.map_config_id_to_config_object}")
        # print(StrategyVariables.map_config_id_to_config_object)

        # print(f"Threading active count: {threading.active_count()}")
        time.sleep(5)
        try:
            # IndicatorCalculation.compute_indicators(),
            pass
        except Exception as e:
            logger.error(f"Exception in main screen loop: {e}")
            print(f"Exception in main screen loop: {e}")
            traceback.print_exc()
        c += 1
    else:
        screen.flag_stopped_all_task = True
        logger.info("Stopped all the tasks, closing the GUI window now")

    print("Screen Closed, Closing the app")
    print("Disconnecting with TWS")

    # Want to kill the whole process and all the active threads right away here
    logger.debug("Screen Closed, Closing the app")
    logger.debug("Disconnecting with TWS")

    app.disconnect()

    print("Disconnected with TWS")
    logger.debug("Disconnected with TWS")

count = 0
rep = 2
sleep_time = 1
while count < rep:
    print(f"Exiting Gracefully in {rep - count} seconds")
    count += 1
    time.sleep(1)
else:
    os._exit(0)


"""
Ctrl + K + Ctrl + 0: fold all levels (namespace, class, method, and block)
Ctrl + K + Ctrl + 1: namespace / @Component(For Angular)
Ctrl + K + Ctrl + 2: class / methods
Ctrl + K + Ctrl + 3: methods / blocks
Ctrl + K + Ctrl + 4: blocks / inner blocks
Ctrl + K + Ctrl + [ or Ctrl + k + ]: current cursor block
Ctrl + K + Ctrl + j: UnFold

Ctrl + K + Ctrl + ]: UnFold
"""
