import configparser
import datetime
import logging
import os

# Read the config file
config = configparser.ConfigParser()
config.read("option_scanner_user_inputs.ini")

# Settings from config file
logging_level = config["Logging"]["logging_level"]


def get_logger(name: str):
    logger_name = str(name)

    if logging_level == "DEBUG":
        log_level = logging.DEBUG
    elif logging_level == "INFO":
        log_level = logging.INFO
    elif logging_level == "WARNING":
        log_level = logging.WARNING
    elif logging_level == "ERROR":
        log_level = logging.ERROR
    elif logging_level == "CRITICAL":
        log_level = logging.CRITICAL
    else:
        print("Invalid logging level in config.ini, setting to DEBUG")
        log_level = logging.DEBUG

    # Create a logger
    logger = logging.getLogger(logger_name)

    # Create the log directory if it doesn't exist
    log_dir = rf"Logs"
    os.makedirs(log_dir, exist_ok=True)

    # Create a file handler and specify the log file path
    log_file = rf"{log_dir}\{logger_name}.txt"
    file_handler = logging.FileHandler(log_file)

    # Configure the log format for the file handler
    # formatter = logging.Formatter("%(asctime)s - %(message)s")
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)
    logger.setLevel(log_level)

    return logger


class CustomLogger:
    """
    Custom logger class to log the responses from the cTrader server
    """

    name = f"Log-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    logger = get_logger(name=name)

    name = f"Scanner-Log-{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}"
    scanner_logger = get_logger(name=name)
