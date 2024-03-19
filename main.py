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
from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.database.set_up_db import SetupDatabase
from option_combo_scanner.gui.gui import IsScreenRunning, ScreenGUI
from option_combo_scanner.gui.scanner_inputs_tab import ScannerInputsTab
from option_combo_scanner.gui.utils import Utils
from option_combo_scanner.ibapi_ao.recovery_mode import RecoveryMode
from option_combo_scanner.ibapi_ao.variables import Variables as variables
from option_combo_scanner.indicators_calculator.indicator_calculation import \
    IndicatorCalculation
from option_combo_scanner.strategy.scanner import (Scanner,
                                                   run_option_combo_scanner)
from option_combo_scanner.strategy.strategy_variables import StrategyVariables
from option_combo_scanner.strategy.utilities import StrategyUtils

logger = CustomLogger.logger

def run_indicator_thread():
    # While Screen is open
    while True:
        time.sleep(20)
        try:
            IndicatorCalculation.compute_indicators(), 
        except Exception as e:
            logger.error(f"Exception in indicator thread loop: {e}")
            print(f"Exception in indicator thread loop: {e}")
            traceback.print_exc()

# Method to run app
def run_loop(app):
    app.run()

if __name__ == "__main__":

    def run_screen():
        global screen

        # Create Screen GUIat

        screen = ScreenGUI()

        # Run the screen main loop, when close set 'variables.screen' as False
        screen.window.mainloop()

        logger.debug("main.py run_sceen: Screen Closed")
    

    # # Check if the user wants to delete the database
    flag_start_in_recovery_mode =   StrategyVariables.flag_recovery_mode

    # Recovery Mode is False, start fresh
    if not flag_start_in_recovery_mode:
        SetupDatabase()

    # Module start time
    module_start_time = datetime.datetime.now(variables.target_timezone_obj)

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
    # TODO - have multi apps later on
    com_variables.cas_app = app

    # flag_start_in_recovery_mode = False

    # # Subscribe the account updates
    # app.reqAccountUpdates(True, variables.account_id)

    # # Start the app in recovery mode
    # if flag_start_in_recovery_mode:
    #     logger.info("Starting the Recovery Mode")

    #     # Run Recovery Mode
    #     RecoveryMode.run(module_start_time)

    #     # Recovery Mode is done, now start the app
    #     logger.debug("Completed recovery, starting app")

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

    # StrategyUtils.update_the_values_for_order_preset_table()

    # monitor_order_preset_obj = MonitorOrderPreset()

    StrategyVariables.screen = screen

    c = 0

    logger.debug("GUI Screen Initialized")
    print("GUI Screen Initialized")

    # TODO - Restart later on
    # Creating a separate thread
    scanner_thread = threading.Thread(target=run_option_combo_scanner, daemon=True)
    scanner_thread.start()

    indicator_thread = threading.Thread(target=run_indicator_thread, daemon=True)
    indicator_thread.start()
        
    # Creating the Scanner Object
    # scanner_input = ScannerInputsTab(scanners_object)
    # While Screen is open
    while IsScreenRunning.flag_is_screen_running:
        time.sleep(1)
        try:
            # IndicatorCalculation.compute_indicators(), 
            pass
        except Exception as e:
            logger.error(f"Exception in main screen loop: {e}")
            print(f"Exception in main screen loop: {e}")
            traceback.print_exc()
            # tidi tracevacl

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
    print(f"Exiting Gracefully in {rep-count} seconds")
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