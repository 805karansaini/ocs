import configparser
import datetime
import time

import pytz

from option_combo_scanner.database.sql_queries import SqlQueries
from option_combo_scanner.ibapi.execution import ExecutionFilter
from option_combo_scanner.ibapi_ao.executions import get_execution_details
from option_combo_scanner.ibapi_ao.variables import Variables as variables

# Read the config file
config = configparser.ConfigParser()
config.read("option_scanner_user_inputs.ini")

timezone_config = config["TimeZone"]
target_timezone = timezone_config["target_timezone"]

from option_combo_scanner.custom_logger.logger import CustomLogger

logger = CustomLogger.logger


class RecoveryMode:
    def __init__(self):
        pass

    @staticmethod
    def run(module_start_time=None):
        print("\nSetting up recovery mode")
        print("Fetching order status (can take upto 10 seconds)")
        logger.info("Setting up recovery mode")
        logger.info("Fetching order status (can take upto 10 seconds)")

        # Get execution details
        # get_execution_details(module_start_time)

        # Requeset the open orders
        variables.app.reqOpenOrders()

        time.sleep(5)

        # Check all orders in the db, any order that has a last update time < module start time, mark those as cancelled
        RecoveryMode.mark_order_cancelled(module_start_time)

    @staticmethod
    def mark_order_cancelled(module_start_time):
        values_dict = {"OrderStatus": "Cancelled"}

        # where clause, LastUpdateTime < module_start_time and OrderStatus != Filled
        where_clause = (
            f"WHERE LastUpdateTime < '{module_start_time}' AND OrderStatus != 'Filled'"
        )

        SqlQueries.update_orders(values_dict, where_clause)
