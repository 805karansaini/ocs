import configparser
import os
import time

import mysql.connector as mc
from mysql.connector import errorcode, pooling
from mysql.connector.locales.eng import client_error

from option_combo_scanner.custom_logger.logger import CustomLogger

# Get the logger
logger = CustomLogger.logger

# Read the config file
config = configparser.ConfigParser()
# Get the directory of the current script
script_dir = os.path.dirname(os.path.abspath(__file__))
option_scanner_user_inputs_ini_file_path = os.path.join(script_dir, "..",  "..", "option_scanner_user_inputs.ini")

config.read(option_scanner_user_inputs_ini_file_path)

dbconfig = config["Database"]


class DatabaseConnector:
    def __init__(self, pool_size=8):
        # DB Config
        self.dbconfig = dbconfig
        self.pool_size = pool_size
        self.connection_pool = self.create_connection_pool()

    def create_connection_pool(self):
        # Create a connection pool
        return mc.pooling.MySQLConnectionPool(
            pool_name="DatabaseServer",
            pool_size=self.pool_size,
            **self.dbconfig,
            pool_reset_session=True,
            autocommit=True,
        )

    def get_connection_to_database(self):
        retries = 0

        while retries < 10:
            try:
                connection = self.connection_pool.get_connection()
                return connection
            except Exception as exp:
                print(
                    f"Try No. {retries+1}/10... Unable to connect to database. Retrying in 0.1 seconds. Error: {exp}"
                )
                logger.error(
                    f"Try No. {retries+1}/10... Unable to connect to database. Retrying in 0.1 seconds. Error: {exp}"
                )
                retries += 1
                time.sleep(0.1)

        # Return None
        return None
