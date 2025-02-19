import configparser
import copy
import datetime
import os
import time

import mysql.connector
import pytz

from option_combo_scanner.custom_logger.logger import CustomLogger
from option_combo_scanner.database.db_setup_queries import all_queries, query0, query1

# Get the logger
logger = CustomLogger.logger
# Read the config file
config = configparser.ConfigParser()
# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
option_scanner_user_inputs_ini_file_path = os.path.join(
    script_dir, "..", "..", "option_scanner_user_inputs.ini"
)

config.read(option_scanner_user_inputs_ini_file_path)

dbconfig = config["Database"]
timezone_config = config["TimeZone"]

target_timezone = timezone_config["target_timezone"]
target_timezone_obj = pytz.timezone(target_timezone)

import pprint


class SetupDatabase:
    def __init__(
        self,
    ):
        self.dbconfig = copy.deepcopy(dbconfig)
        self.dbconfig_without_database = copy.deepcopy(dbconfig)
        del self.dbconfig_without_database["database"]

        self.drop_database()
        print("Dropped Database")
        logger.info("Dropped Database")

        self.create_database()
        print("Created Database")
        logger.info("Created Database")

        self.setup_database()
        print("Created Tables")
        logger.info("Created Tables")

    def drop_database(
        self,
    ):
        connection = mysql.connector.connect(**self.dbconfig_without_database)
        cursor = connection.cursor()

        try:
            cursor.execute(query0)
            connection.commit()
        except mysql.connector.Error as err:
            print(f"Exception occured while dropping database: {err}")
            logger.error(
                f"Query: {query0}\nException occured while dropping database: {err}"
            )

        cursor.close()
        connection.close()

    def create_database(
        self,
    ):
        connection = mysql.connector.connect(**self.dbconfig_without_database)
        cursor = connection.cursor()

        try:
            cursor.execute(query1)
            connection.commit()
        except mysql.connector.Error as err:
            print(f"Exception occured while creating database: {err}")
            logger.error(
                f"Query: {query1}\nException occured while creating database: {err}"
            )

        cursor.close()
        connection.close()

    def setup_database(
        self,
    ):
        connection = mysql.connector.connect(**self.dbconfig)
        cursor = connection.cursor()

        for query in all_queries:
            try:
                cursor.execute(
                    query,
                )
                connection.commit()
            except mysql.connector.Error as err:
                print(f"Exception occured while creating tables: {err}")
                logger.error(
                    f"Query: {query}\nException occured while creating tables: {err}"
                )

        connection.commit()
        cursor.close()
        connection.close()
