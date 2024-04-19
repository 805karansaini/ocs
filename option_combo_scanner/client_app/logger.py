import datetime
import logging
import os


class CustomLogger:
    """
    Custom logger class to log the responses from the cTrader server
    """

    def __init__(self, name: str):
        self.logger_name = str(name)

        # Set the logging level
        self.log_level = logging.DEBUG

        # Create a logger
        self.logger = logging.getLogger(self.logger_name)

        # Current Date in YYYYMMDD
        current_date = datetime.datetime.now().strftime("%Y%m%d")
        
        # Create the log directory if it doesn't exist
        log_dir = fr"Logs\{current_date}"
        os.makedirs(log_dir, exist_ok=True)

        # Create a file handler and specify the log file path
        log_file = rf"{log_dir}\{self.logger_name}.txt"

        file_handler = logging.FileHandler(log_file, mode="w")

        # Configure the log format for the file handler
        formatter = logging.Formatter("%(asctime)s - %(message)s")
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        self.logger.addHandler(file_handler)
        self.logger.setLevel(self.log_level)
