import datetime
import os
import threading
import time
import tkinter as tk
from tkinter import messagebox

from custom_logger.logger import CustomLogger
from database.set_up_db import SetupDatabase
from gui.gui import IsScreenRunning, ScreenGUI
from gui.utils import Utils
from ibapi_ao.app import IBapi
from ibapi_ao.recovery_mode import RecoveryMode
from ibapi_ao.variables import Variables as variables
from strategy.monitor_order_preset import MonitorOrderPreset
from strategy.strategy_variables import StrategyVariables
from strategy.utilities import StrategyUtils

logger = CustomLogger.logger


def ask_for_user_confirmation():
    """
    Do the user want to start app in recovery mode?
    or delete the database and start fresh?
    """
    # Create a tkinter root window
    root = tk.Tk()
    root.withdraw()

    # Show a messagebox with the confirmation message
    result = messagebox.askyesno(
        "Start in Recovery Mode?",
        "Do you want to start application in 'Recovery Mode'?\n\nClick 'Yes' to start in Recovery Mode, 'No' to clear the database and start fresh.",
    )

    # Check the user's response
    if result:
        # User clicked 'Yes'
        logger.debug("Recovery mode confirmed.")
        print("Recovery mode confirmed.")
    else:
        # User clicked 'No'
        logger.debug("Recovery mode canceled.")
        print("Recovery mode canceled.")

    # Destroy the root window
    root.destroy()

    return result


if __name__ == "__main__":

    def run_screen():
        global screen

        # Create Screen GUI
        screen = ScreenGUI()

        # Run the screen main loop, when close set 'variables.screen' as False
        screen.window.mainloop()

        logger.debug("main.py run_sceen: Screen Closed")

    logger.debug("Please Confirm the start mode")
    print("Please Confirm the start mode")

    # Check if the user wants to delete the database
    flag_start_in_recovery_mode = ask_for_user_confirmation()

    # Recovery Mode is False, start fresh
    if not flag_start_in_recovery_mode:
        SetupDatabase()

    # Module start time
    module_start_time = datetime.datetime.now(variables.target_timezone_obj)

    # Main App TWS Object
    app = IBapi()

    # Expose app to ibapi_ao.variables
    variables.app = app

    # Subscribe the account updates
    app.reqAccountUpdates(True, variables.account_id)

    # Start the app in recovery mode
    if flag_start_in_recovery_mode:
        logger.info("Starting the Recovery Mode")

        # Run Recovery Mode
        RecoveryMode.run(module_start_time)

        # Recovery Mode is done, now start the app
        logger.debug("Completed recovery, starting app")

    # Start Screen Now
    screen_thread = threading.Thread(target=run_screen)
    screen_thread.start()

    # Wait for screen to start
    while not IsScreenRunning.flag_is_screen_running:
        logger.debug("Intializing GUI Screen")
        print("Intializing GUI Screen")
        time.sleep(0.2)
    else:
        time.sleep(1)

    StrategyUtils.update_the_values_for_order_preset_table()

    monitor_order_preset_obj = MonitorOrderPreset()

    StrategyVariables.screen = screen

    c = 0

    logger.debug("GUI Screen Initialized")
    print("GUI Screen Initialized")

    # While Screen is open
    while IsScreenRunning.flag_is_screen_running:
        try:
            time.sleep(0.5)
            try:
                # Update Order Book from the database
                screen.order_book_tab_object.update_order_book_table()
            except Exception as exp:
                logger.error(
                    f"Exception in main-update_order_book_table exp: {exp}"
                )

            try:
                # Accumulate the latest Prices
                price = Utils.get_prices_for_order_presets()
            except Exception as exp:
                logger.error(
                    f"Exception in main-get_prices_for_order_presets exp: {exp}"
                )

            try:
                # Get the latest values dataframe for order preset table
                order_preset_table_values_df = (
                    Utils.create_latest_order_preset_values_dataframe(price)
                )
            except Exception as exp:
                logger.error(
                    f"Exception in main-create_latest_order_preset_values_dataframe exp: {exp}"
                )

            try:
                # Update prices in GUI
                screen.order_preset_tab_object.update_order_preset_table(
                    order_preset_table_values_df
                )
            except Exception as exp:
                logger.error(f"Exception in main-update_order_preset_table exp: {exp}")

        except Exception as e:
            logger.error(f"Exception in main screen loop: {e}")

        c += 1
    else:
        screen.flag_stopped_all_task = True
        logger.info("Stopped all the tasks, closing the GUI window now")

    print("Screen Closed, Closing the app")
    print("Disconnecting with TWS")

    # Want to kill the whole process and all the active threads right away here
    logger.debug("Screen Closed, Closing the app")
    logger.debug("Disconnecting with TWS")

    app.close_api_connection()

    print("Disconnected with TWS")
    logger.debug("Disconnected with TWS")

count = 0
rep = 10
sleep_time = 1
while count < rep:
    print(f"Exiting Gracefully in {rep-count} seconds")
    count += 1
    time.sleep(1)
else:
    os._exit(0)
